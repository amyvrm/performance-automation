#!groovy

node('aws&&docker')
{
    def jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"
    def prod = "Performance-Scenario-Test"
    def dev = "development-Performance-Scenario-Test"
    if ("${env.JOB_BASE_NAME}" == "Performance-Test-Parallel")
    {
        echo "Production pipeline......."
        def perf_pipeline = prod
    }
    else
    {
        echo "Development pipeline......"
        def perf_pipeline = dev
    }
    def perf_pipeline = "Performance-Scenario-Test"
    def pipeline_num = "${env.BUILD_NUMBER}"
    def stats = "stats.html"
    def graph = "band.png"
    def machine_info = "manifest.json"
    def pkg = "update-packages"
    def msg = ""
    def user_name = "None"
    def dsru_name = ""
    def scenario = ["Server_Upload", "Server_Download", "Client_Download"]
    def dsru_file = ""
//     def scenario = ["Server_Upload", "Server_Download"]

    wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }
    deleteDir()

    try
    {
        stage("Get Package URL") {
            if (params.PACKAGE_URL == "") {
                stage("Sign and Upload") {
                    try {
                        def sign = build job: "DSRU Automation/Sign and Upload/Sample DSRU", quietPeriod : 5
//                         def sign = build job: "DSRU_DOWNLOAD_SIGN_UPLOAD",  quietPeriod: 5

                        s_build = sign.number
                        dsru_file = sign.buildVariables.vsu
                        echo "Signing JOB Build : ${s_build}"
                        echo "Build Value  : ${dsru_file}"

                        // dslabs_auto_monitoring
                        slackSend channel: "dslabs_auto_monitoring", color: "good",
                                  message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                        // dsruhandover
                        slackSend channel: "dsruhandover", color: 'good',
                                  message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                    }
                    catch(e) {
                        currentBuild.result = "FAILURE"
                        // dslabs_auto_monitoring
                        slackSend channel: 'dslabs_auto_monitoring', color: 'danger',
                                   message: "${currentBuild.currentResult} in 'Sign and Upload' Stage\n${msg}"
                        // dsruhandover
                        slackSend channel: "dsruhandover", color: 'danger',
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
                dsru_name = call_scenario_test("Server_Upload", perf_pipeline, "${pipeline_num}", dsru_file)
            }, Server_Download: {
                echo "Waiting 30 sec before running parallel scenario pipeline"
                sleep time: 30, unit: 'SECONDS'
                dsru_name = call_scenario_test("Server_Download", perf_pipeline, "${pipeline_num}", dsru_file)
            },
            Client_Download: {
                echo "Waiting 60 before running parallel scenario pipeline"
                sleep time: 60, unit: 'SECONDS'
                dsru_name = call_scenario_test("Client_Download", perf_pipeline, "${pipeline_num}", dsru_file)
            },
            failFast: false
        }

        currentBuild.result = 'SUCCESS'
        stage("Slack Message") {
            jfrog_url = "${jfrog_url}/${dsru_name}/${pipeline_num}"
            msg = "Pipeline: <${env.BUILD_URL}|Perform Automation> User: ${user_name}\n"
            msg += "${currentBuild.result}: :green_circle:\n\n"
            for (int i = 0; i < scenario.size(); i++) {
                stats_file =  "${scenario[i]}_${stats}"
                graph_file =  "${scenario[i]}_${graph}"
                machine_file =  "${scenario[i]}_${machine_info}"
                echo "stats_file: ${stats_file}"
                echo "graph_file: ${graph_file}"
                echo "machine_file: ${machine_file}"
                msg += "${scenario[i]} Iteration Stats: <${jfrog_url}/${stats_file}|Table>\n"
                msg += "${scenario[i]} Average Iteration: <${jfrog_url}/${graph_file}|Bar Chart>\n"
                msg += "${scenario[i]} Machine info: <${jfrog_url}/${machine_file}|Json File>\n\n"
            }
            // dslabs_auto_monitoring
            slackSend channel: 'dslabs_auto_monitoring', color: "good", message: "${msg}"
            // dsruhandover
            slackSend channel: "dsruhandover", color: 'good', message: "${msg}"
        }
    }
    catch (e) {
        currentBuild.result = 'FAILURE'
        msg = "Pipeline: <${env.BUILD_URL}|Perform Automation> User: ${user_name}\n"
        msg += "${currentBuild.result}: :dot-red:\nError: ${e}\n"
        msg += "Infrastructure may be kept for Debug Purpose."

        // dslabs_auto_monitoring
        slackSend channel: 'dslabs_auto_monitoring', color: "good", message: "${msg}"
        // dsruhandover
        slackSend channel: "dsruhandover", color: 'good', message: "${msg}"
        println(e)
        throw e
    }
}

def call_scenario_test(scenario, perf_pipeline, pipeline_num, dsru_file) {
    //scenario = "Server_Upload"
    echo "Calling ${scenario} test"
    perf = build quietPeriod: 5, job: perf_pipeline,
                 parameters: [string(name: 'DSM_PACKAGE_URL', value: params.DSM_PACKAGE_URL),
                    credentials(description: 'DSM License Key for Automation', name: 'DSM_LICENSE_KEY', value: params.DSM_LICENSE_KEY),
                    extendedChoice(name: 'AGENTS', value: params.AGENTS),
                    text(name: 'AGENT_DOWNLOAD_URL', value: params.AGENT_DOWNLOAD_URL),
                    string(name: 'PACKAGE_URL', value: dsru_file),
                    string(name: 'SCENARIO', value: scenario),
                    booleanParam(name: 'DEBUG', value: params.DEBUG),
                    string(name: 'PARENT_PIPELINE_NUMBER', value: "${pipeline_num}")]

    echo "Build Number: ${perf.number}"
//     copyArtifacts filter: "**/*.html, **/*.png, **/*.json", projectName: perf_pipeline, selector: specific("${perf.number}")
//     echo "Copied ${scenario} Artifacts"
    return perf.buildVariables.pkg_name
}
