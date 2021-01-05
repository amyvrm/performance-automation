#!groovy

import groovy.json.JsonSlurper
def nodeLabel = params.JENKINS_NODE_LABEL ?: 'aws&&docker'
final TERRAFORM_DIR ="terraformHC"
final MAIN_DIR ="terraformHC"
final OUTPUT_DIR ="terraformHC/staging_template"

@NonCPS
def jsonParse(def json) { new groovy.json.JsonSlurper().parseText(json) }

node(nodeLabel)
{
	timestamps
	{
		timeout(time: 24, unit: 'HOURS')
		{
			withCredentials([[$class: 'AmazonWebServicesCredentialsBinding', accessKeyVariable: 'AWS_ACCESS_KEY_ID',credentialsId: 'STAGING_AWS', secretKeyVariable: 'AWS_SECRET_ACCESS_KEY']])
		    {
				def infra_branch = "master"
				def dsm_package_url = params.DSM_PACKAGE_URL
				def dsm_license_key = params.DSM_LICENSE_KEY
				def agents = params.AGENTS
				def agents_download_urls = params.AGENT_DOWNLOAD_URL
				def destroy_param = "null"
				def debug = params.DEBUG
                def dsru_file

				def displayName
				def jsonText
				def all_ids = ""
				def agent_instances = ""
                def target_path = "Temp"
				def bucket_name = "perf-auto-pkg"
				def machine_info = "manifest.json"
				def nexus_url = "https://dsnexus.trendmicro.com:8443/nexus/repository/dslabs/performance-test/${env.JOB_BASE_NAME}/${env.BUILD_NUMBER}"
				def stats = "stats.html"
				def graph = "band.png"
				def pkg = "update-packages"
				def msg = ""
				def user_name = "None"
				def scenario = ["Server_Upload", "Server_Download", "Client_Download"]

                wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }
				deleteDir()
				dsmVersion =  dsm_package_url.substring(dsm_package_url.lastIndexOf('-') + 1, dsm_package_url.length())

                if (params.PACKAGE_URL == "") {
                    stage("Sign and Upload") {
                        try {
                            def sign = build job: "DSRU_DOWNLOAD_SIGN_UPLOAD",  quietPeriod: 5

                            s_build = sign.number
                            dsru_file = sign.buildVariables.vsu
                            echo "Signing JOB Build : ${s_build}"
                            echo "Build Value  : ${dsru_file}"

                            //slackSend channel: "debug_amit", color: "good",
                            slackSend channel: "dslabs_auto_monitoring", color: "good",
                                      message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                        }
                        catch(e) {
                            currentBuild.result = "FAILURE"
                            //slackSend channel: 'debug_amit', color: 'danger',
                            slackSend channel: 'dslabs_auto_monitoring', color: 'danger',
                                       message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                            error("${e}")
                        }
                    }
                }
                else {
                    dsru_file = params.PACKAGE_URL
                }

				withCredentials([string(credentialsId: dsm_license_key, variable: 'dsm_key')]) {
					try {
						currentBuild.displayName = "#${env.BUILD_NUMBER}"
						stage('Git Code')
						{
							checkout changelog: false, poll: false, scm: [$class         : 'GitSCM',
																		branches         : [[name: "${infra_branch}"]],
																		extensions       : [[$class: 'RelativeTargetDirectory', relativeTargetDir: TERRAFORM_DIR]],
																		userRemoteConfigs: [[credentialsId: 'su-dslabs-automation-token',
																							url           : 'https://dsgithub.trendmicro.com/dslabs/performance-automation.git']]]
						}
                        def machineIP = sh(script:'''/sbin/ifconfig eth0 | grep 'inet ' | awk '{print $2}' | cut -d: -f2 ''', returnStdout:true).trim()
                        dockerOptions = "-v /tmp:/tmp -h ${machineIP}"
                        def containerName = "dsru-decrypt:latest"

                        stage('Build Docker')
                        {
                            sh "docker build -t ${containerName} -f ${MAIN_DIR}/DockerfileSign ."
                        }
                        docker.image("${containerName}").inside("${dockerOptions}")
                        {
                            dir(MAIN_DIR) {
                                stage('Download and Decrypt Package') {
                                    withCredentials([usernamePassword(credentialsId: 'dslabs-nexus', usernameVariable: "NEX_USER", passwordVariable: 'NEX_PASS')]) {
                                        sh("python src/download_nexus.py --url ${dsru_file} --path ${pkg} --uname ${NEX_USER} --pwd ${NEX_PASS}")
							            sh "ls -1 ${WORKSPACE}/${MAIN_DIR}/${pkg}"
                                    }
							        checkout scm
                                    dir('dsrusigning')
                                    {
                                        git branch: 'master', credentialsId: 'su-dslabs-automation-token',
                                        url: 'https://git@dsgithub.trendmicro.com/dslabs/dsrusigning.git'
                                    }
                                    dsru_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${pkg}/*.dsru", returnStdout: true).trim()
							        sh "java -jar dsrusigning/DSRUCrypt.jar decrypt ${dsru_file}/"
							    }
							    stage('Parse Package') {
							        sh("python src/parse_update.py ${pkg}")
							        sh "ls ${pkg}"
							    }
                            }
                        }

						def infraImage = docker.build("infra-image", "./${TERRAFORM_DIR}")

						infraImage.inside {
						    dir(MAIN_DIR) {
						        stage('Download Tools') {
						            withCredentials([[$class: 'AmazonWebServicesCredentialsBinding',
						                               accessKeyVariable: 'ACCESS_KEY',
							                           credentialsId: 'dslabs-jenkins-automation-credentials',
							                           secretKeyVariable: 'SECRET_KEY']]) {
                                        sh ("python src/get_pkg_frm_s3.py --access_key $ACCESS_KEY \
                                                                      --secret_key $SECRET_KEY \
                                                                      --bucket $bucket_name \
                                                                      --path $target_path")
                                    }
                                    echo "Downloaded packages:"
                                    sh "ls ${target_path}"
                                }

                                stage('Create Infra') {
							        echo "Initialize automation"
									sh "python initializeProcesszone.py --agents \"${agents}\""
									sh "terraform init processzone"

							        echo 'Validate automation'
									sh "python validateAutomation.py --access_key \"${AWS_ACCESS_KEY_ID}\" --secret_key \"${AWS_SECRET_ACCESS_KEY}\" --agent_urls \"${agents_download_urls}\" --dsm_url \"${dsm_package_url}\" --dsm_license \"${dsm_key}\""

							        echo 'Plan automation'
								    sh "python planAutomation.py --access_key \"${AWS_ACCESS_KEY_ID}\" --secret_key \"${AWS_SECRET_ACCESS_KEY}\" --agent_urls \"${agents_download_urls}\" --dsm_url \"${dsm_package_url}\" --dsm_license \"${dsm_key}\""

							        echo 'Apply automation'
									sh "python applyAutomation.py"

							        echo 'Grab login info in JSON'
								    sh "terraform output -json > ${machine_info}"
							    }

							    stage('Perf Test') {
							        withCredentials([usernamePassword(credentialsId: 'dslabs-nexus', usernameVariable: "NEX_USER",
							                                      passwordVariable: 'NEX_PASS')]) {
                                        sh("python src/perform_scenario.py --access_key ${AWS_ACCESS_KEY_ID} \
                                                                       --secret_key ${AWS_SECRET_ACCESS_KEY} \
                                                                       --machine_info ${machine_info} \
                                                                       --dsm_version ${dsmVersion} \
                                                                       --stats ${stats} \
                                                                       --graph ${graph} \
                                                                       --path ${pkg} \
                                                                       --uname ${NEX_USER} \
                                                                       --pwd ${NEX_PASS}")
                                    }
                                    sh "ls -1"
                                    archiveArtifacts allowEmptyArchive: true,
						            artifacts: '${stats}, ${graph}, update-info/status.txt'
							    }
							    stage('Get EC2 IDs') {
								    jsonText = jsonParse(readFile("${machine_info}"))
                                    def dsm_id = jsonText['dsm-rhel-id']['value']
                                    def sg_id = jsonText['sg-id']['value']

                                    if (agents.contains('Windows Server 2019')) {
                                        agent_instances = agent_instances + ',' + jsonText['dsa-windows-id']['value']
                                    }
                                    if (agents.contains('Windows Server 2019 A2')) {
                                        agent_instances = agent_instances + ',' + jsonText['dsa-windows-id-2']['value']
                                    }
                                    jsonText = null
                                    all_ids = dsm_id+','+ sg_id + agent_instances
                                    destroy_param = 'AWS_RESOURCES = '+all_ids
                                    writeFile file: 'tear_down_params.txt', text: "${destroy_param}"
								}
								jsonText = null
							}
							currentBuild.result = 'SUCCESS'
							stage("Nexus Upload") {
							    withCredentials([usernamePassword(credentialsId: 'dslabs-nexus', usernameVariable: "NEX_USER",
							                                      passwordVariable: 'NEX_PASS')]) {
                                    def manifest_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${machine_info}", returnStdout: true).trim()
                                    def mfile = sh(script: "basename ${manifest_file}", returnStdout: true).trim()
                                    sh "curl --user ${NEX_USER}:${NEX_PASS} --upload-file ${manifest_file} ${nexus_url}/${mfile} --fail -v"

                                    for (int i = 0; i < scenario.size(); i++) {
                                        stats_file =  "${scenario[i]}_${stats}"
                                        graph_file =  "${scenario[i]}_${graph}"
                                        // Get table name
                                        html_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${stats_file}", returnStdout: true).trim()
                                        fname = sh(script: "basename ${html_file}", returnStdout: true).trim()
                                        // Get bar chart name
                                        png_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${graph_file}", returnStdout: true).trim()
                                        gfile = sh(script: "basename ${png_file}", returnStdout: true).trim()
                                        // Upload file
                                        sh "curl --user ${NEX_USER}:${NEX_PASS} --upload-file ${html_file} ${nexus_url}/${fname} --fail -v"
                                        sh "curl --user ${NEX_USER}:${NEX_PASS} --upload-file ${png_file} ${nexus_url}/${gfile} --fail -v"
                                    }
                                }
                            }
							stage("Slack message") {
							    msg = "Pipeline: <${env.BUILD_URL}|Perform Automation> User: ${user_name}\n"
							    msg += "${currentBuild.result}: :green_circle:\n\n"
							    for (int i = 0; i < scenario.size(); i++) {
							        stats_file =  "${scenario[i]}_${stats}"
                                    graph_file =  "${scenario[i]}_${graph}"
                                    msg += "${scenario[i]} Iteration Stats: <${nexus_url}/${stats_file}|Table>\n"
                                    msg += "${scenario[i]} Average Iteration: <${nexus_url}/${graph_file}|Bar Chart>\n\n"
                                }
							    msg += "Manifest File: <${nexus_url}/${machine_info}|Machine Details>"
							    slackSend channel: 'dslabs_auto_monitoring', color: "good", message: "${msg}"
							    //slackSend channel: 'debug_amit', color: "good", message: "${msg}"
							}
						}
						stage("Destroy Infra") {
                            if("${debug}" == 'true'){
                                echo "Debug Enabled [Infrastructure Preserved]"
                            }
                            else{
                                echo "Debug Disabled [Destroying Infrastructure....]"

                                build job: 'Staging Automation/tear-down-dsm-dsa-infrastructure',
                                parameters: [
                                    string(name: 'INFRA_BRANCH', value: "development"),
                                    string(name: 'AWS_RESOURCES', value: all_ids)
                                ]
                            }
                        }
					}
					catch (e)
					{
					    currentBuild.result = 'FAILURE'
					    msg = "Pipeline: <${env.BUILD_URL}|Perform Automation> User: ${user_name}\n"
					    msg += "${currentBuild.result}: :dot-red:\nError: ${e}\n"
					    msg += "Infrastructure may be kept for Debug Purpose."
						slackSend channel: 'dslabs_auto_monitoring', color: "good", message: "${msg}"
						//slackSend channel: 'debug_amit', color: "good", message: "${msg}"
						println(e)
						throw e
					} 
					finally
					{
						archiveArtifacts allowEmptyArchive: true,
						artifacts: '**/manifest.json,**/tear_down_params.txt'
					}
				}
			}
		}
	}
}