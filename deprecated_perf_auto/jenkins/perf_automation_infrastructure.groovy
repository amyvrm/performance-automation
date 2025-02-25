#!groovy
//final TERRAFORM_DIR ="terraformHC"

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
        if (!(Scenario in ["Server_Upload", "Server_Download", "Client_Download"])) {
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
            def dsru_url = ""

        // Terraform related Pipeline Variables
            def iac_path = "deprecated_perf_auto/iac_src"
            def iac_working_dir = "${iac_path}/src"
            def plan = "create.tfplan"
            def iac_path_dsm_dsa = "${iac_path}/processzone"
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
            //def manifest_file_path = "${WORKSPACE}/${iac_path}/${manifest_file}"
            //def manifest_file_pattern = "${WORKSPACE}/${iac_path}/**.json"
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

            def jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"

        try 
        {

            stage('Git checkout')
            {
                    checkout scm
                    withCredentials([file(credentialsId: 'perf_dslabs_automation_pem', variable: 'PEM_FILE_PATH')]){
	            	sh "cat ${PEM_FILE_PATH} > processzone/dslabs_automation.pem"
	                }
                    withCredentials([file(credentialsId: 'perf_TerraformDemo_pem', variable: 'PEM_FILE_PATH')]){
	            	sh "cat ${PEM_FILE_PATH} > processzone/TerraformDemo.pem"
	                }
            }

           wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }


            def infraImage = docker.build("infra-image", "-f deprecated_perf_auto/docker/Dockerfile .")
            
                infraImage.inside
                {
                        
                    stage('Get Tools')
                    {
                        sh "ls -ls ${iac_path_dsm_dsa}"
                        
                        sh ("python ${iac_working_dir}/get_pkg_frm_s3.py --access_key ${S3_ACCESS_KEY}    \
                                                                        --secret_key ${S3_SECRET_KEY}    \
                                                                        --bucket ${bucket_name}          \
                                                                        --path ${target_path}")
                        
                        sh "ls -ls ${target_path}"
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
                            sh "ls -la ${iac_path_dsm_dsa}"
                            
                            echo "Terraform Plan"
                            
                            sh "terraform -chdir=${iac_path_dsm_dsa} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'all_agent_urls=${agents_download_urls}\' -var=\'dsm_redhat_url=${dsm_package_url}\' -var=\'dsm_license=${dsm_key}\' -var=\'random_num=${env.BUILD_NUMBER}\' -out ${plan_dsm_dsa}"
                            
                            echo "Terraform Apply"

                            sh "terraform -chdir=${iac_path_dsm_dsa} apply -auto-approve ${plan_dsm_dsa}"
                    }

                    stage('DSM infra information')
                    {
                        dir("${iac_path_dsm_dsa}")
                        {
                            sh "ls -la"
                            sh "pwd"
                            sh "terraform output -json"
                            sh "terraform output -json > ${manifest_file}"
                            archiveArtifacts allowEmptyArchive: true, artifacts: "${manifest_file}"
                        }
                    }

                    stage('Tear Down Infrastructure - IDs')
                    {
                            script
                            {
                                echo "Reading the manifest file"

                                def manifestFile = readFile("${iac_path_dsm_dsa}/${manifest_file}")

                                echo "Manifest File : ${manifestFile}"

                                def jsonSlurper = new groovy.json.JsonSlurper()
                                def jsonText = jsonSlurper.parseText(manifestFile)

                                echo "Tear Down IDs : ${jsonText}"

                                def keysToExtract = ['dsa-windows-id', 'dsa-windows-id-2', 'dsm-rhel-id']

                                all_ids = keysToExtract.collect { key -> jsonText[key]?.value }.findAll { it != null }.join(', ')

                                destroy_param = 'AWS_RESOURCES = ' + all_ids
                            
                                echo "Destroy Manifest File : ${destroy_param}"

                            }
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
    }
}