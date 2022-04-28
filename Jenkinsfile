#!groovy

node('aws&&docker')
{
    // SEC
	withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY',
					   credentialsId: 'STAGING_AWS', secretKeyVariable: 'AWS_SECRET_KEY']])
    {
        deleteDir()
        // Pipeline Variables
        def iac_path="iac_src"
        def plan = "create.tfplan"

        currentBuild.displayName = "${env.BUILD_NUMBER}"
        currentBuild.result = 'SUCCESS'
        stage('Git checkout')
        {
            checkout scm
        }
        def infraImage = docker.build("infra-image")
        infraImage.inside
        {
            stage('Create Infra')
            {
                sh "terraform -chdir=${iac_path} init"
                sh "terraform -chdir=${iac_path} validate"
                sh "terraform -chdir=${iac_path} plan -var=\'access_key=${AWS_ACCESS_KEY}\' -var=\'secret_key=${AWS_SECRET_KEY}\' -out ${plan}"
                sh "terraform -chdir=${iac_path} apply -auto-approve ${plan}"
            }
        }
}
