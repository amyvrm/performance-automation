#!groovy
final TERRAFORM_DIR ="terraformHC"

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
        def scenario = params.SCENARIO

        // DSRU Related Pipeline Variables
            def dsm_package_url = params.DSM_PACKAGE_URL
            def dsm_license_key = params.DSM_LICENSE_KEY
            def agents = params.AGENTS
            def agents_download_urls = params.AGENT_DOWNLOAD_URL
            def package_url = params.PACKAGE_URL
            def dsru_url = ""

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
            def manifest_file_path = "${iac_path}/${manifest}"
            def manifest_file_pattern = "${iac_path}/**.json"
            def destroy_param = ""

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
            all_ids = ""

            def jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"
        
        if (!(Scenario in ["Server_Upload", "Server_Download", "Client_Download"])) 
        {
    	    error ("Scenario unknown")
	    }

        if (params.PARENT_PIPELINE_NUMBER == "0")
        {
            pipeline_num = "individual_${env.BUILD_NUMBER}"
        }

        try 
        {
            wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }

            stage('Deploying infrastructure') 
            {
					infrajob = build job: 'Infra_Create_Perf_Scenario', 
						parameters: [
							string(name: 'DSM_PACKAGE_URL', value: dsm_package_url),
							credentials(description: 'DSM License Key for Automation', name: 'DSM_LICENSE_KEY', value: 'AUTOMATION_DSM_LICENSE_KEY'),
							string(name: 'AGENTS', value: agents),
							string(name: 'AGENT_DOWNLOAD_URL', value: agents_download_urls),
                            string(name: 'SCENARIO', value: scenario)
						]
			}

            stage('Collect DSM DSA infrastructure Info') 
            {
                sleep(time:15 ,unit:"SECONDS")
				
				job_number = infrajob.getNumber().toString()
				
				copyArtifacts filter: '**/*.json, **/*.txt', projectName: 'Infra_Create_Perf_Scenario', selector: specific(job_number.toString())

                echo "Manifest file is copied"
                sh "ls -la ${WORKSPACE}"

                echo "Reading the manifest file"
                echo "Manifest File : ${manifest_file}"

                def manifestFile = readFile("${manifest_file}")
                echo "Manifest File : ${manifestFile}"
                def jsonSlurper = new groovy.json.JsonSlurper()
                def jsonText = jsonSlurper.parseText(manifestFile)		
										
				dsm_ip = jsonText['dsm-public-ip']['value']
				dsm_user = jsonText['dsm-login-user']['value']
				dsm_password = jsonText['dsm-login-password']['value']

                echo "DSM IP: ${dsm_ip}"
                echo "DSM User: ${dsm_user}"
                echo "DSM Password: ${dsm_password}"
            }

            stage('Run Performance Test') 
            {
                job_number = infrajob.getNumber().toString()
                perf_test = build job: 'Performance_Scenario_Test',
                parameters: [
                    string(name: 'SCENARIO', value: scenario),
                    string(name: 'PACKAGE_URL', value: "${package_url}"),
                    string(name: 'JOB_NUMBER', value: job_number)
                ]
            }

            stage('Collect Automation Machine Tear Down infrastructure') 
            {
                sleep(time:15 ,unit:"SECONDS")

                perf_test_number = perf_test.getNumber().toString()

                copyArtifacts filter: '**/*.txt', projectName: 'Performance_Scenario_Test', selector: specific(perf_test_number.toString())

                def tearDown = readFile("tear_down_params_automation.txt")

                echo "Tear Down Params: ${tearDown}"

				all_ids = tearDown.drop(16)

                echo "All IDs: ${all_ids}"
            }

            stage('Collect Tear Down infrastructure') 
            {
                def tearDown = readFile("tear_down_params.txt")

                echo "Tear Down Params: ${tearDown}"

				all_ids = all_ids + ", " + tearDown.drop(16)

                echo "All IDs: ${all_ids}"
            }

            stage('Tear Down infrastructure') 
            {
					if("${debug}" == 'false'){
                        echo "Debug disabled. Destroying Infrastructure...."
						
						build job: 'Performance-Scenario-teardown',
						parameters: [
							string(name: 'AWS_RESOURCES', value: all_ids)
						]
					}
					else{
						echo "Debug enabled. Infrastructure Preserved."
					}
					jsonText = null
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



            
