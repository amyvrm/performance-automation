#!groovy

node('aws&&docker')
{
    def dsru_file
    def nexus_url = "https://dsnexus.trendmicro.com:8443/nexus/repository/dslabs/performance-test"
    def perf_pipeline = "Perf-Automation/test_pipelines/test-perf-scenario"
    def stats = "stats.html"
    def graph = "band.png"
    def machine_info = "manifest.json"
    def pkg = "update-packages"
    def msg = ""
    def user_name = "None"
    def dsru_name = ""
//    def scenario = ["Server_Upload", "Server_Download", "Client_Download"]
    def scenario = ["Server_Upload", "Server_Download"]

    wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }
    deleteDir()
    dsmVersion =  dsm_package_url.substring(dsm_package_url.lastIndexOf('-') + 1, dsm_package_url.length())

    try {
        stage("Get Package URL") {
            if (params.PACKAGE_URL == "") {
                stage("Sign and Upload") {
                    try {
                        def sign = build job: "DSRU_DOWNLOAD_SIGN_UPLOAD",  quietPeriod: 5

                        s_build = sign.number
                        dsru_file = sign.buildVariables.vsu
                        echo "Signing JOB Build : ${s_build}"
                        echo "Build Value  : ${dsru_file}"

                        slackSend channel: "debug_amit", color: "good",
                        //slackSend channel: "dslabs_auto_monitoring", color: "good",
                                  message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                    }
                    catch(e) {
                        currentBuild.result = "FAILURE"
                        slackSend channel: 'debug_amit', color: 'danger',
                        //slackSend channel: 'dslabs_auto_monitoring', color: 'danger',
                                   message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                        error("${e}")
                    }
                }
            }
            else {
                dsru_file = params.PACKAGE_URL
            }
        }

        stage("Parallel Perf Test") {
            parallel Server_Upload: {
                dsru_name = server_upload(perf_pipeline, dsru_file)
            }, Server_Download: {
                echo "Waiting 2 min before running parallel scenario pipeline"
                sleep time: 2, unit: 'MINUTES'
                dsru_name = server_download(perf_pipeline, dsru_file)
            },
            Client_Download: {
                echo "Waiting 2 min before running parallel scenario pipeline"
                sleep time: 2, unit: 'MINUTES'
                dsru_name = client_download(perf_pipeline, dsru_file)
            },
            failFast: false
        }

        currentBuild.result = 'SUCCESS'
        stage("Nexus Upload") {
            nexus_url = "${nexus_url}/${dsru_name}/${env.BUILD_NUMBER}"
            withCredentials([usernamePassword(credentialsId: 'dslabs-nexus', usernameVariable: "NEX_USER",
                                              passwordVariable: 'NEX_PASS')]) {

                for (int i = 0; i < scenario.size(); i++) {
                    stats_file =  "${scenario[i]}_${stats}"
                    graph_file =  "${scenario[i]}_${graph}"
                    machine_file =  "${scenario[i]}_${machine_info}"
                    // Get table name
                    html_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${stats_file}", returnStdout: true).trim()
                    fname = sh(script: "basename ${html_file}", returnStdout: true).trim()
                    // Get bar chart name
                    png_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${graph_file}", returnStdout: true).trim()
                    gfile = sh(script: "basename ${png_file}", returnStdout: true).trim()
                    // Get Machine info
                    def manifest_file = sh(script: "ls -1 ${WORKSPACE}/${MAIN_DIR}/${machine_file}", returnStdout: true).trim()
                    def mfile = sh(script: "basename ${manifest_file}", returnStdout: true).trim()
                    // Upload file
                    sh "curl --user ${NEX_USER}:${NEX_PASS} --upload-file ${html_file} ${nexus_url}/${fname} --fail -v"
                    sh "curl --user ${NEX_USER}:${NEX_PASS} --upload-file ${png_file} ${nexus_url}/${gfile} --fail -v"
                    sh "curl --user ${NEX_USER}:${NEX_PASS} --upload-file ${manifest_file} ${nexus_url}/${mfile} --fail -v"
                }
            }
        }
        stage("Slack Message") {
            msg = "Pipeline: <${env.BUILD_URL}|Perform Automation> User: ${user_name}\n"
            msg += "${currentBuild.result}: :green_circle:\n\n"
            for (int i = 0; i < scenario.size(); i++) {
                stats_file =  "${scenario[i]}_${stats}"
                graph_file =  "${scenario[i]}_${graph}"
                machine_file =  "${scenario[i]}_${machine_info}"
                echo "stats_file: ${stats_file}"
                echo "graph_file: ${graph_file}"
                echo "machine_file: ${machine_file}"
                msg += "${scenario[i]} Iteration Stats: <${nexus_url}/${stats_file}|Table>\n"
                msg += "${scenario[i]} Average Iteration: <${nexus_url}/${graph_file}|Bar Chart>\n"
                msg += "${scenario[i]} Machine info: <${nexus_url}/${machine_file}|Json File>\n\n"
            }
            msg += "Manifest File: <${nexus_url}/${machine_info}|Machine Details>"
            //slackSend channel: 'dslabs_auto_monitoring', color: "good", message: "${msg}"
            slackSend channel: 'debug_amit', color: "good", message: "${msg}"
        }
    }
    catch (e) {
        currentBuild.result = 'FAILURE'
        msg = "Pipeline: <${env.BUILD_URL}|Perform Automation> User: ${user_name}\n"
        msg += "${currentBuild.result}: :dot-red:\nError: ${e}\n"
        msg += "Infrastructure may be kept for Debug Purpose."
        //slackSend channel: 'dslabs_auto_monitoring', color: "good", message: "${msg}"
        slackSend channel: 'debug_amit', color: "danger", message: "${msg}"
        println(e)
        throw e
    }
}

def server_upload(perf_pipeline, dsru_file) {
    scenario = "Server_Upload"
    stats = "stats.html"
    graph = "band.png"
    machine_info = "manifest.json"
    echo "Calling ${scenario} test"
    perf = build quietPeriod: 5, job: perf_pipeline,
                 parameters: [string(name: 'DSM_PACKAGE_URL', value: params.DSM_PACKAGE_URL),
                    credentials(description: 'DSM License Key for Automation', name: 'DSM_LICENSE_KEY', value: params.DSM_LICENSE_KEY),
                    extendedChoice(name: 'AGENTS', value: params.AGENTS),
                    text(name: 'AGENT_DOWNLOAD_URL', value: params.AGENT_DOWNLOAD_URL),
                    string(name: 'PACKAGE_URL', value: dsru_file),
                    string(name: 'SCENARIO', value: scenario),
                    booleanParam(name: 'DEBUG', value: params.DEBUG)]

    copyArtifacts filter: "${scenario}_${stats}, ${scenario}_${graph} ${scenario}_${machine_info}",
                  projectName: perf_pipeline, selector: specific(perf.number)
    return perf.buildVariables.pkg_name
}

def server_download(perf_pipeline, dsru_file) {
    scenario = "Server_Download"
    stats = "stats.html"
    graph = "band.png"
    machine_info = "manifest.json"
    echo "Calling ${scenario} test"
    perf = build quietPeriod: 5, job: perf_pipeline,
                 parameters: [string(name: 'DSM_PACKAGE_URL', value: params.DSM_PACKAGE_URL),
                    credentials(description: 'DSM License Key for Automation', name: 'DSM_LICENSE_KEY', value: params.DSM_LICENSE_KEY),
                    extendedChoice(name: 'AGENTS', value: params.AGENTS),
                    text(name: 'AGENT_DOWNLOAD_URL', value: params.AGENT_DOWNLOAD_URL),
                    string(name: 'PACKAGE_URL', value: dsru_file),
                    string(name: 'SCENARIO', value: scenario),
                    booleanParam(name: 'DEBUG', value: params.DEBUG)]

    copyArtifacts filter: "${scenario}_${stats}, ${scenario}_${graph}, ${scenario}_${machine_info}",
                  projectName: perf_pipeline, selector: specific(perf.number)
    return perf.buildVariables.pkg_name
}

def client_download(perf_pipeline, dsru_file) {
    scenario = "Client_Download"
    stats = "stats.html"
    graph = "band.png"
    machine_info = "manifest.json"
    echo "Calling ${scenario} test"
    echo "Agents: ${params.AGENTS}"
    def value = params.AGENTS.split(",")
    echo "value: ${value}"
	def client_download = "${value[1]},${value[0]}"
	echo "Client Download: ${client_download}"

    perf = build quietPeriod: 5, job: perf_pipeline,
                 parameters: [string(name: 'DSM_PACKAGE_URL', value: params.DSM_PACKAGE_URL),
                    credentials(description: 'DSM License Key for Automation', name: 'DSM_LICENSE_KEY', value: params.DSM_LICENSE_KEY),
                    extendedChoice(name: 'AGENTS', value: client_download),
                    text(name: 'AGENT_DOWNLOAD_URL', value: params.AGENT_DOWNLOAD_URL),
                    string(name: 'PACKAGE_URL', value: dsru_file),
                    string(name: 'SCENARIO', value: scenario),
                    booleanParam(name: 'DEBUG', value: params.DEBUG)]

    copyArtifacts filter: "${scenario}_${stats}, ${scenario}_${graph}, ${scenario}_${machine_info}",
                  projectName: perf_pipeline, selector: specific(perf.number)
    return perf.buildVariables.pkg_name
}
