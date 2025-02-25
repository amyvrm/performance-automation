#!groovy
def nodeLabel = params.JENKINS_NODE_LABEL ?: 'aws&&docker'
final TERRAFORM_DIR ="terraformHC"
final MAIN_DIR ="terraformHC"
final OUTPUT_DIR ="terraformHC/staging_template"

node(nodeLabel) {
	timestamps {
		timeout(time: 24, unit: 'HOURS') {
			withCredentials([[$class       : 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID',
							credentialsId: 'STAGING_AWS', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY']]) {
				
				def aws_resources = params.AWS_RESOURCES
				def terraform_dir = "deprecated-perf-auto/iac_destroy"
				
				def displayName
				def infrastructure_branch = params.INFRASTRUCTURE_BRANCH
				deleteDir()
				
				try {
					
					currentBuild.displayName = "#${env.BUILD_NUMBER}"
					
					stage('Download infrastructure automation') {
						checkout changelog: false, poll: false, scm: [$class           : 'GitSCM',
																	branches         : [[name: infrastructure_branch]],
																	extensions       : [[$class: 'RelativeTargetDirectory', relativeTargetDir: TERRAFORM_DIR]],
																	userRemoteConfigs: [[credentialsId: 'su-dslabs-automation-token',
																						url          : 'https://dsgithub.trendmicro.com/dslabs/performance-automation.git']]]
					}
					
					
					def infraImage = docker.build("infra-image", "-f ./${TERRAFORM_DIR}/docker/Dockerfile .")
					
					
					infraImage.inside {
						
						stage('Destroying resources') {
							dir(MAIN_DIR){
								sh """
								    python ${terraform_dir}/destroy_infra.py \
								    --access_key "${AWS_ACCESS_KEY_ID}" \
								    --secret_key "${AWS_SECRET_ACCESS_KEY}" \
								    --resource_list "${aws_resources}" \
								    --terraform_dir "${terraform_dir}"
								"""
							}
						}
						currentBuild.result = 'SUCCESS'
					}
				}
				catch (e) {
					currentBuild.result = 'FAILURE'
					println(e)
					throw e
				}
			}
		}
	}
}
	