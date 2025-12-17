#!groovy
//final TERRAFORM_DIR ="terraformHC"

// Helper method to parse JSON
@NonCPS
def parseJson(String jsonString) {
    def jsonSlurper = new groovy.json.JsonSlurper()
    return jsonSlurper.parseText(jsonString)
}

def captureTeardownIds(iac_path_dsm_dsa, manifest_file)
{
    // This function can be expanded if needed
    script
    {
        echo "Reading the manifest file"
        def manifestFile = readFile("${iac_path_dsm_dsa}/${manifest_file}")
        echo "Manifest File : ${manifestFile}"
        
        def instanceIds = []
        def destroy_param = ""
        
        try {
            // Try to extract from terraform output first
            def jsonText = parseJson(manifestFile)
            echo "Tear Down IDs from output: ${jsonText}"
            def keysToExtract = jsonText.keySet().findAll { key -> 
                key.startsWith('dsa-windows-id') || 
                key.startsWith('dsa-windows_agent-id') || 
                key.startsWith('dsm-rhel-id')
            }                                  
            // Collect the values from matched keys
            def all_ids = keysToExtract.collect { key -> jsonText[key]?.value }
                                      .findAll { it != null } // Remove nulls
                                      .join(', ')
            echo "All IDs from output: ${all_ids}"
            // Extract only the instance IDs
            instanceIds = all_ids.tokenize(',').collect { id -> id.trim().find(/i-[a-zA-Z0-9]+/)}.findAll { it != null }
        } catch (Exception e) {
            echo "Failed to parse terraform output, falling back to state file: ${e.message}"
        }
        
        // Fallback: extract from state file if output parsing failed or is empty
        if (instanceIds.isEmpty()) {
            echo "Extracting instance IDs from terraform state..."
            def stateIds = sh(script: "cat ${iac_path_dsm_dsa}/created_instance_ids.txt 2>/dev/null || echo ''", returnStdout: true).trim()
            if (stateIds) {
                instanceIds = stateIds.split('\n').findAll { it.trim() && it.startsWith('i-') }
                echo "Instance IDs from state: ${instanceIds.join(', ')}"
            }
        }
        
        if (instanceIds.isEmpty()) {
            echo "WARNING: No instance IDs found. Manual cleanup may be required."
            destroy_param = 'AWS_RESOURCES = NONE_FOUND'
        } else {
            destroy_param = 'AWS_RESOURCES = ' + instanceIds.join(', ')
        }
    
        echo "Destroy Manifest File : ${destroy_param}"
        return destroy_param
    }
}

node('aws&&docker')
{
    // SEC
	withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY',
					   credentialsId: 'STAGING_AWS', secretKeyVariable: 'AWS_SECRET_KEY'],
					   [$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'S3_ACCESS_KEY',
				       credentialsId: 'dslabs-jenkins-automation-credentials', secretKeyVariable: 'S3_SECRET_KEY'],
					   string(credentialsId: 'dsdeploy-artifactory-token', variable: 'LABS_JFROG_TOKEN'),
                       			string(credentialsId: 'jenkins-webhook-workflow', variable: 'teams_webhook'),
					   string(credentialsId: dsm_license_key, variable: 'dsm_key')])
    {
        deleteDir()
        def scenario = params.SCENARIO
        if (!(scenario in ["Server_Upload", "Server_Download", "Client_Download"])) {
    	    error ("Scenario unknown")
	    }
        if (params.PARENT_PIPELINE_NUMBER == "0")
        {
            pipeline_num = "individual_${env.BUILD_NUMBER}"
        }
        else
        {
            pipeline_num = "parent_${params.PARENT_PIPELINE_NUMBER}"
        }

        // DSRU Related Pipeline Variables
            def dsm_package_url = params.DSM_PACKAGE_URL
            def dsm_license_key = params.DSM_LICENSE_KEY
            def agents = params.AGENTS
            def agents_download_urls = params.AGENT_DOWNLOAD_URL
            def dsru_url = params.PACKAGE_URL

        // Terraform related Pipeline Variables
            def iac_path = "iac_src"
            def iac_working_dir = "${iac_path}/src"
            def plan = "create.tfplan"
            def iac_path_dsm_dsa = "processzone"
            def plan_dsm_dsa = "create_dsm_dsa.tfplan"
            def destroy_dsm_dsa = "dsm_dsa_destroy.tfplan"
            def destroy_auto = "auto_destroy.tfplan"

        // S3 bucket Related Pipeline Variables
            def bucket_name = "perf-auto-pkg"
            def target_path = "${iac_path_dsm_dsa}/Temp"

        // manifest file naming
            def manifest =  "manifest.json"
            def manifest_file =  "${scenario}_${manifest}"
            def manifest_file_path = "${iac_path}/${manifest_file}"
            def manifest_file_pattern = "${iac_path}/**.json"
            def image_name = "perf-auto:${env.BUILD_NUMBER}"
            def dockerfile = 'docker/DockerfileSign'
            def destroy_param = ""

            echo "Working Directory: ${WORKSPACE}"

        // DSRU related Pipeline Variables
            def dsru_path = "${iac_path}/update-packages"
            def dsru_folder = "update-packages"
            def dsru_file = ""
            def pkg_name = ""
            def dsmVersion =  dsm_package_url.substring(dsm_package_url.lastIndexOf('-') + 1, dsm_package_url.length())

        // General Pipeline Variables
            def user_name = ""
            def msg = ""
            def stats = "stats.html"
            def graph = "band.png"
            def stats_file =  "${scenario}_stats.html"
            def graph_file =  "${scenario}_band.png"
            def all_ids = ""
            def applyResult = ""

            def server_rules
            def client_rules

            def rule_id_length = params.NO_OF_RULES


            def individual_rule_test = params.INDIVIDUAL_RULE_TEST


            def jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"

        try 
        {

            stage('Git checkout')
            {
                    checkout scm
                    withCredentials([file(credentialsId: 'perf_dslabs_automation_pem', variable: 'PEM_FILE_PATH')]){
	            	sh "cat ${PEM_FILE_PATH} > processzone/dslabs_automation.pem"
	                }
                    dir('dsrusigning')
                    {
                        git branch: 'master', credentialsId: 'su-dslabs-automation-token',
                        url: 'https://git@dsgithub.trendmicro.com/dslabs/dsrusigning.git'
                    }
            }

           wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }


           sign_image = docker.build("${image_name}", "-f ${dockerfile} .")

            sign_image.inside
            {
                stage('Download DSRU Package')
                {
                    sh "python ${iac_working_dir}/download_jfrog.py --url ${dsru_url} --path ${dsru_path} --jfrog_token ${LABS_JFROG_TOKEN}"
                }

                stage('Decrypt DSRU Package')
                {
                    dsru_file = sh(script: "ls -1 ${WORKSPACE}/${dsru_path}/*.dsru", returnStdout: true).trim()
	        	    sh "java -jar dsrusigning/DSRUCrypt.jar decrypt ${dsru_file}/"
	        	    env.pkg_name = sh(script: "basename ${dsru_file}", returnStdout: true).trim()
                    echo "${env.pkg_name}"
                    sh "ls -la ${WORKSPACE}/${dsru_path}"
                }
            }

            def infraImage = docker.build("infra-image", "-f docker/DockerFileStage .")
            
                infraImage.inside
                {

                    stage('Extract DSRU Rules')
                    {
                        script {
                            def output = sh(script: "python ${iac_working_dir}/parse_update.py ${dsru_path}", returnStdout: true).trim()
                            echo "Output: ${output}"
                            def outputList = output.split(' ', 2)
                            def count = outputList[0]
                            def ids = outputList[1]
                            echo "Count: ${count}"
                            echo "IDs: ${ids}"
                            env.count = count
                            echo "Count: ${env.count}"
                            env.ruleids = ids
                            sh "ls -la ${dsru_path}"
                        }
                    }

                    echo "rule_id_length ${rule_id_length}"

                    if (rule_id_length != "" && (individual_rule_test == true || individual_rule_test == false))
                    {
                        env.count = rule_id_length
                        echo "Count_: ${env.count}"
                    }
                    else if (rule_id_length == "" && individual_rule_test == false)
                    {
                        env.count = 1
                        echo "Count_2: ${env.count}"
                    }
                    else
                    {
                        env.count = env.count
                        echo "Count_3: ${env.count}"
                    }

                    stage('Validate Scenario with Rules')
                    {
                        script {
                            def output = sh(script: "python3 ${iac_working_dir}/extract_Dsrurules.py --stats ${stats} --graph ${graph} --path ${dsru_path} --scenario ${scenario} --identifiers '${env.ruleids}'", returnStdout: true).trim()
                            echo "Output: ${output}"
                            // Parse the output to get the server and client rules counts
                            server_rules = output.find(/server_rules=\d+/)?.split('=')[1]
                            client_rules = output.find(/client_rules=\d+/)?.split('=')[1]

                            echo "server_rules: ${server_rules}"
                            echo "client_rules: ${client_rules}"
                        }
                    }

                    if (scenario == "Client_Download" && client_rules == "0") {
                        echo "No Client_Download rules available"
                        currentBuild.result = "SUCCESS"
                        return
                    } else if ((scenario == "Server_Upload" || scenario == "Server_Download") && server_rules == "0") {
                        echo "No Server rules available"
                        currentBuild.result = "SUCCESS"
                        return 
                    }

                    stage('Get Tools')
                    {
                        sh ("python ${iac_working_dir}/get_pkg_frm_s3.py --access_key ${S3_ACCESS_KEY}    \
                                                                        --secret_key ${S3_SECRET_KEY}    \
                                                                        --bucket ${bucket_name}          \
                                                                        --path ${target_path}")
                    }

                    stage('Initialize Infra automation') 
                    {
                			sh "terraform -chdir=${iac_path_dsm_dsa} init"
                	}

                    stage('Validate Infra automation') 
                    {
                            sh "terraform -chdir=${iac_path_dsm_dsa} validate"
                	}


                    stage('Infra Plan and Apply - DSM, DSA and Test')
                    {
                            echo "Count: ${env.count}"

                            sh "ls -la ${iac_path_dsm_dsa}"
                            
                            echo "Terraform Plan"
                            
                            sh "terraform -chdir=${iac_path_dsm_dsa} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'all_agent_urls=${agents_download_urls}\' -var=\'dsm_redhat_url=${dsm_package_url}\' -var=\'dsm_license=${dsm_key}\' -var=\'random_num=${env.BUILD_NUMBER}\' -var=\'instance_count=${env.count}\' -out ${plan_dsm_dsa}"
                            
                            echo "Terraform Apply"

                            // Try apply and capture exit code
                            applyResult = sh(script: "terraform -chdir=${iac_path_dsm_dsa} apply -auto-approve ${plan_dsm_dsa}", returnStatus: true)

                            echo "Terraform Apply Result: ${applyResult}"
                    }

                    stage('DSM infra information')
                    {
                        dir("${iac_path_dsm_dsa}")
                        {
                            // Use || true to ensure we continue even if output fails
                            sh "terraform output -json || echo '{}'"
                            sh "terraform output -json > ${manifest_file} || echo '{}' > ${manifest_file}"
                            archiveArtifacts allowEmptyArchive: true, artifacts: "${manifest_file}"
                        }
                    }

                    stage('Tear Down Infrastructure - IDs')
                    {
                        destroy_param = captureTeardownIds(iac_path_dsm_dsa, manifest_file)
                    }

                    stage('Tear Down Infrastructure - Manifest')
                    {

                        writeFile file: 'tear_down_params.txt', text: destroy_param
                        
                        archiveArtifacts allowEmptyArchive: true, artifacts: '**/tear_down_params.txt'

                    }
                }

        }
        catch(e)
        {
            currentBuild.result = "FAILURE"
            println(e)
			throw e
        }
        finally
        {
            // Always capture instance IDs from state, even on partial failure
            // Fail the stage if apply failed, but after capturing IDs
            if (((scenario == "Server_Upload" || scenario == "Server_Download") && server_rules != 0 ) || (scenario == "Client_Download" && client_rules != 0))
            {
                echo "No ${scenario} rules available"
                currentBuild.result = "SUCCESS"
                return
            }
            else if (applyResult != 0) {
                dir("${iac_path_dsm_dsa}")
                {
                    // Use || true to ensure we continue even if output fails
                    sh "terraform output -json || echo '{}'"
                    sh "terraform output -json > ${manifest_file} || echo '{}' > ${manifest_file}"
                    archiveArtifacts allowEmptyArchive: true, artifacts: "${manifest_file}"
                }
                error("Terraform apply failed with exit code ${applyResult}, but instance IDs have been captured")

                captureTeardownIds(iac_path_dsm_dsa, manifest_file)
            }
        }
    }
}