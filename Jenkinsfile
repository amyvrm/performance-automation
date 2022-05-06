#!groovy

node('aws&&docker')
{
    // SEC
	withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY',
					   credentialsId: 'STAGING_AWS', secretKeyVariable: 'AWS_SECRET_KEY'],
					   [$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'S3_ACCESS_KEY',
				       credentialsId: 'dslabs-jenkins-automation-credentials', secretKeyVariable: 'S3_SECRET_KEY'],
					   usernamePassword(credentialsId: 'su-dslabs-creds', usernameVariable: 'NEXUS_USR',
					                                                    passwordVariable: 'NEXUS_PWD'),
					   string(credentialsId: dsm_license_key, variable: 'dsm_key')])
    {
        deleteDir()
        // Pipeline Variables
        def scenario = params.SCENARIO
        def debug = params.DEBUG
        def pipeline_num = params.PARENT_PIPELINE_NUMBER
        if (pipeline_num == "0")
        {
            pipeline_num = "individual_${env.BUILD_NUMBER}"
        }

        // Terraform related Pipeline Variables
        def iac_path = "iac_src"
        def iac_working_dir = "${iac_path}/src"
        def plan = "create.tfplan"
        def iac_path_dsm_dsa = "processzone"
        def plan_dsm_dsa = "create_dsm_dsa.tfplan"

        // DSRU Related Pipeline Variables
        def dsm_package_url = params.DSM_PACKAGE_URL
        def dsm_license_key = params.DSM_LICENSE_KEY
        def agents = params.AGENTS
        def agents_download_urls = params.AGENT_DOWNLOAD_URL
        def dsru_url = params.PACKAGE_URL
        def dsru_path = "${iac_path}/update-packages"
        def dsru_folder = "update-packages"
        def dsru_file = ""
        def pkg_name = ""
        def dsmVersion =  dsm_package_url.substring(dsm_package_url.lastIndexOf('-') + 1, dsm_package_url.length())

        // S3 bucket Related Pipeline Variables
        def bucket_name = "perf-auto-pkg"
        def target_path = "${iac_path_dsm_dsa}/Temp"

        // General Pipeline Variables
        def user_name = ""
        def msg = ""
        def stats = "stats.html"
        def graph = "band.png"
        def stats_file =  "${scenario}_stats.html"
        def graph_file =  "${scenario}_band.png"
        def manifest_file =  "${scenario}_manifest.json"
        def manifest_file_path = "${WORKSPACE}/${iac_path}/${manifest_file}"
        def manifest_file_pattern = "${WORKSPACE}/${iac_path}/*.json"
        def image_name = "perf-auto:${env.BUILD_NUMBER}"
        def dockerfile = 'DockerfileSign'
//         def nexus_url_dslabs = "https://dsnexus.trendmicro.com:8443/nexus/repository/dslabs"
//         def nexus_url = "${nexus_url_dslabs}/${env.JOB_BASE_NAME}/${env.BUILD_NUMBER}"
        def nexus_url = "https://dsnexus.trendmicro.com:8443/nexus/repository/dslabs/performance-test"
        def teams_webhook = 'https://trendmicro.webhook.office.com/webhookb2/d6c82240-57b1-41b5-84e8-09def3921052@3e04753a-ae5b-42d4-a86d-d6f05460f9e4/JenkinsCI/b131747740c34e90b770e2a911dea18f/5110c51b-5ae9-4caa-a0a8-aafc778ce125'

        currentBuild.displayName = "${env.BUILD_NUMBER}"
        currentBuild.result = 'SUCCESS'

        stage('Git checkout')
        {
            checkout scm
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
                sh "python ${iac_working_dir}/download_nexus.py --url ${dsru_url} --path ${dsru_path} --uname ${NEXUS_USR} --pwd ${NEXUS_PWD}"
            }
            stage('Decrypt DSRU Package')
            {
                dsru_file = sh(script: "ls -1 ${WORKSPACE}/${dsru_path}/*.dsru", returnStdout: true).trim()
			    sh "java -jar dsrusigning/DSRUCrypt.jar decrypt ${dsru_file}/"
				env.pkg_name = sh(script: "basename ${dsru_file}", returnStdout: true).trim()
				nexus_url = "${nexus_url}/${env.pkg_name}/${pipeline_num}"
				echo "nexus_url: ${nexus_url}"
            }
            stage('Parse DSRU Package')
            {
                sh("python ${iac_working_dir}/parse_update.py ${dsru_path}")
                sh "ls -1 ${dsru_path}"
            }
        }

        def infraImage = docker.build("infra-image")
        infraImage.inside
        {
            stage('Get Tools')
            {
                sh ("python ${iac_working_dir}/get_pkg_frm_s3.py --access_key ${S3_ACCESS_KEY}    \
                                                                 --secret_key ${S3_SECRET_KEY}    \
                                                                 --bucket ${bucket_name}          \
                                                                 --path ${target_path}")
            }
            stage('Infra Creation - DSM, DSA and Test')
            {
                sh "terraform -chdir=${iac_path_dsm_dsa} init"
                sh "terraform -chdir=${iac_path_dsm_dsa} validate"
                sh "terraform -chdir=${iac_path_dsm_dsa} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'all_agent_urls=${agents_download_urls}\' -var=\'dsm_redhat_url=${dsm_package_url}\' -var=\'dsm_license=${dsm_key}\' -var=\'random_num=${env.BUILD_NUMBER}\' -out ${plan_dsm_dsa}"
                sh "terraform -chdir=${iac_path_dsm_dsa} apply -auto-approve ${plan_dsm_dsa}"
            }
            stage('DSM infra information')
            {
                dir("${iac_path_dsm_dsa}")
                {
                    sh "terraform output -json > ${manifest_file_path}"
                    archiveArtifacts allowEmptyArchive: true, artifacts: "${manifest_file_pattern}"
                }
            }
            stage('Automation machine')
            {
                sh "terraform -chdir=${iac_path} init"
                sh "terraform -chdir=${iac_path} validate"
                sh "terraform -chdir=${iac_path} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'machine_file=${manifest_file_path}\' -var=\'dsmVersion=${dsmVersion}\' -var=\'stats=${stats}\' -var=\'graph=${graph}\' -var=\'dsru_path=${dsru_folder}\' -var=\'nexus_url=${nexus_url}\' -var=\'nexus_user=${NEXUS_USR}\' -var=\'nexus_pass=${NEXUS_PWD}\' -var=\'scenario=${scenario}\' -var=\'random_num=${env.BUILD_NUMBER}\' -var=\'webhook=${teams_webhook}\' -var=\'jenkins_url=${env.BUILD_URL}\' -var=\'build_user=${user_name}\' -var=\'pipeline_num=${pipeline_num}\' -out ${plan}"
                sh "terraform -chdir=${iac_path} apply -auto-approve ${plan}"
            }
            stage('Send Teams Message')
            {
                sh("python3 src/team_msg.py --scenario ${scenario}           \
                                            --webhook \'${teams_webhook}\'   \
                                            --jenkins_url ${env.BUILD_URL}   \
                                            --build_user \'${user_name}\'        \
                                            --stats ${stats}                 \
                                            --graph ${graph}                 \
                                            --nexus_url ${nexus_url}         \
                                            --pipeline_num ${env.BUILD_NUMBER}")
            }
        }
    }
}
