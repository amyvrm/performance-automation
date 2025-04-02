#!groovy

node('aws&&docker')
{
    def jfrog_url = "https://jfrog.trendmicro.com/artifactory/dslabs-performance-generic-test-local"
    def perf_pipeline = "Performance-Scenario-Control"
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

    wrap([$class: 'BuildUser']) { user_name = "${env.BUILD_USER}" }
    deleteDir()

    try
    {
        stage("Get Package URL") {
            if (params.PACKAGE_URL == "") {
                stage("Sign and Upload") {
                    try {
                        def sign = build job: "DSRU Automation/Sign and Upload/Sample DSRU", quietPeriod : 5
                        s_build = sign.number
                        dsru_file = sign.buildVariables.vsu
                        echo "Signing JOB Build : ${s_build}"
                        echo "Build Value  : ${dsru_file}"
                    }
                    catch(e) {
                        currentBuild.result = "FAILURE"
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
    }
    catch (e) {
        currentBuild.result = 'FAILURE'
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
                    string(name: 'PARENT_PIPELINE_NUMBER', value: "${pipeline_num}"),
                    string(name: 'INFRASTRUCTURE_BRANCH', value: params.INFRASTRUCTURE_BRANCH),
                    string(name: 'RULE_ID', value: params.RULE_ID),
                    booleanParam(name: 'INDIVIDUAL_RULE_TEST', value: params.INDIVIDUAL_RULE_TEST)]

    echo "Build Number: ${perf.number}"
    return perf.buildVariables.pkg_name
}