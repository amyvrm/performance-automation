#!groovy

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
        def job_number = params.JOB_NUMBER

        def pipeline_num = "parent_${params.PARENT_PIPELINE_NUMBER}" 
        if (params.PARENT_PIPELINE_NUMBER == "0")
        {
            pipeline_num = "individual_${env.BUILD_NUMBER}"
        }

        // Terraform related Pipeline Variables
            def iac_path = "iac_src"
            def iac_working_dir = "${iac_path}/src"
            def plan = "create.tfplan"
            def destroy_auto = "auto_destroy.tfplan"

        // manifest file naming
            def manifest =  "manifest.json"
            def manifest_file =  "${scenario}_${manifest}"
            def manifest_file_path = "${WORKSPACE}/${iac_path}/${manifest_file}"
            
        // DSRU Related Pipeline Variables    
            def dsru_path = "${iac_path}/update-packages"
            def dsru_folder = "update-packages"
            def dsru_url = ""
            def dsru_file = ""
            def dsmVersion =  dsm_package_url.substring(dsm_package_url.lastIndexOf('-') + 1, dsm_package_url.length())

        // General Pipeline Variables
            def user_name = ""
            def msg = ""
            def stats = "stats.html"
            def graph = "band.png"
            def stats_file =  "${scenario}_stats.html"
            def graph_file =  "${scenario}_band.png"

            wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }
            def image_name = "perf-auto:${env.BUILD_NUMBER}"
            def dockerfile = 'docker/DockerfileSign'

            def jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"

        try
        {
            stage('Git checkout')
            {
                checkout scm
                dir('dsrusigning')
                {
                    git branch: 'master', credentialsId: 'su-dslabs-automation-token',
                    url: 'https://git@dsgithub.trendmicro.com/dslabs/dsrusigning.git'
                }
            }


            stage("Get Package URL")
            {
                if (params.PACKAGE_URL == "")
                {
                    stage("Sign and Upload")
                    {
                        def sign = build job: "DSRU Automation/Sign and Upload/Sample DSRU", quietPeriod : 5
                        s_build = sign.number
                        dsru_url = sign.buildVariables.vsu
                        echo "Signing JOB Build : ${s_build}"
                        echo "Build Value  : ${dsru_url}"
                    }
                }
                else
                {
                    dsru_url = params.PACKAGE_URL
                }
            }

            stage('Get Manifest file')
            {
                    echo "Copying the manifest file"
                    echo "Job Number : ${job_number}"
                    copyArtifacts filter: '**/*.json', projectName: 'Infra_Create_Perf_Scenario', selector: specific(job_number.toString()), target: "${WORKSPACE}/${iac_path}"
                    echo "Manifest file is copied"
                    sh "ls -la ${WORKSPACE}/${iac_path}"
            }

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
	        		jfrog_url = "${jfrog_url}/${env.pkg_name}/${pipeline_num}"
	        		echo "jfrog_url: ${jfrog_url}"
                }

                stage('Parse DSRU Package')
                {
                    sh("python ${iac_working_dir}/parse_update.py ${dsru_path}")
                    sh "ls -la ${dsru_path}"
                }
            }

            def infraImage = docker.build("infra-image", "-f docker/Dockerfile .")

            infraImage.inside
            {
                stage('Automation machine')
                {
                        sh "ls -la ${iac_path}"

                        sh "terraform -chdir=${iac_path} init"

                        sh "terraform -chdir=${iac_path} validate"

                        sh "terraform -chdir=${iac_path} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'manifest_file_path=${manifest_file_path}\' -var=\'manifest_file=${manifest}\' -var=\'dsmVersion=${dsmVersion}\' -var=\'stats=${stats}\' -var=\'graph=${graph}\' -var=\'dsru_path=${dsru_folder}\' -var=\'jfrog_url=${jfrog_url}\' -var=\'jfrog_token=${LABS_JFROG_TOKEN}\' -var=\'scenario=${scenario}\' -var=\'random_num=${env.BUILD_NUMBER}\' -out ${plan}"

                        sh "terraform -chdir=${iac_path} apply -auto-approve ${plan}"
                }

                stage('Automation machine information')
                {
                    dir("${iac_path}")
                    {
                        sh "ls -la"
                        sh "pwd"
                        sh "terraform output -json"
                        sh "terraform output -json > ${manifest_file}"
                        archiveArtifacts allowEmptyArchive: true, artifacts: "${manifest_file}"
                    }
                }

                stage('Automation machine Infrastructure - IDs')
                {
                    script
                    {
                        echo "Reading the manifest file"
                        def manifestFile = readFile("${iac_path}/${manifest_file}")
                        echo "Manifest File : ${manifestFile}"
                        def jsonSlurper = new groovy.json.JsonSlurper()
                        def jsonText = jsonSlurper.parseText(manifestFile)
                        echo "Tear Down IDs : ${jsonText}"
                        def keysToExtract = ['performance_auto_machine_id', 'run_automation_id']
                        all_ids = keysToExtract.collect { key -> jsonText[key]?.value }.findAll { it != null }.join(', ')
                        destroy_param = 'AWS_RESOURCES = ' + all_ids

                        echo "Destroy Manifest File : ${destroy_param}"
                    }
                }

                stage('Tear Down Infrastructure - Manifest')
                {
                        writeFile file: 'tear_down_params_automation.txt', text: destroy_param

                        archiveArtifacts allowEmptyArchive: true, artifacts: '**/tear_down_params_automation.txt'
                }

                /*stage('Send Teams Message')
                {
                sh("python3 ${iac_working_dir}/team_msg.py --scenario ${scenario}   \
		                            --pipeline_name \'${env.JOB_BASE_NAME}\'              \
                                            --webhook \'${teams_webhook}\'              \
		                            --status \'${currentBuild.currentResult}\'              \
                                            --jenkins_url ${env.BUILD_URL}          \
                                            --build_user \'${user_name}\'           \
                                            --stats \'${stats}\'                        \
                                            --graph \'${graph}\'                        \
                                            --manifest_file \'${manifest_file}\'        \
                                            --jfrog_url \'${jfrog_url}\'                \
                                            --build_number ${pipeline_num}")
                }*/
            }
        }
        catch (e)
        {
            currentBuild.result = 'FAILURE'
            println(e)
            throw e
        }
    }
}