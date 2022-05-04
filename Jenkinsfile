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
        def machine_info = "manifest.json"
        def stats_file =  "${scenario}_stats.html"
        def graph_file =  "${scenario}_band.png"
        def machine_file =  "${scenario}_manifest.json"
        def image_name = "perf-auto:${env.BUILD_NUMBER}"
        def dockerfile = 'DockerfileSign'

        currentBuild.displayName = "${env.BUILD_NUMBER}"
        currentBuild.result = 'SUCCESS'
        /*
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
            }
            stage('Parse DSRU Package')
            {
                sh("python ${iac_working_dir}/parse_update.py ${dsru_path}")
                sh "ls -1 ${dsru_path}"
            }
        }
        */
        mfile = "${WORKSPACE}/${iac_path_dsm_dsa}/${machine_file}"
        echo "manifest file : ${mfile}"
        if (fileExists("${mfile}"))
        {
            def infraImage = docker.build("infra-image")
            infraImage.inside
            {
    //             stage('Get Tools')
    //             {
    //                 sh ("python ${iac_working_dir}/get_pkg_frm_s3.py --access_key ${S3_ACCESS_KEY}    \
    //                                                                  --secret_key ${S3_SECRET_KEY}    \
    //                                                                  --bucket ${bucket_name}          \
    //                                                                  --path ${target_path}")
    //             }
    //             stage('Infra Creation - DSM, DSA and Test')
    //             {
    //                 sh "terraform -chdir=${iac_path_dsm_dsa} init"
    //                 sh "terraform -chdir=${iac_path_dsm_dsa} validate"
    //                 sh "terraform -chdir=${iac_path_dsm_dsa} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'all_agent_urls=${agents_download_urls}\' -var=\'dsm_redhat_url=${dsm_package_url}\' -var=\'dsm_license=${dsm_key}\' -var=\'random_num=${env.BUILD_NUMBER}\' -out ${plan_dsm_dsa}"
    //                 sh "terraform -chdir=${iac_path_dsm_dsa} apply -auto-approve ${plan_dsm_dsa}"
    //                 sh "terraform output -json > ${iac_path}/${machine_file}"
    //                 archiveArtifacts allowEmptyArchive: true, artifacts: "${iac_path_dsm_dsa}/${machine_file}"
    //             }
                stage('Automation machine')
                {
                    sh "terraform -chdir=${iac_path} init"
                    sh "terraform -chdir=${iac_path} validate"
                    sh "terraform -chdir=${iac_path} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -var=\'machine_file=${WORKSPACE}/${iac_path_dsm_dsa}/${machine_file}\' -var=\'dsmVersion=${dsmVersion}\' -var=\'stats=${stats}\' -var=\'graph=${graph}\' -var=\'dsru_path=${dsru_path}\' -var=\'nexus_user=${NEXUS_USR}\' -var=\'nexus_pass=${NEXUS_PWD}\' -var=\'scenario=${scenario}\' -out ${plan}"
                    sh "terraform -chdir=${iac_path} apply -auto-approve ${plan}"
                }
            }
        }
    }
}
