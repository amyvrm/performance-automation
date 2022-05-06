import argparse
import requests
import json


def send_teams_notification(webhook, jenkins_url, build_user, scenario, stats_url, graph_url, pipeline_num):
    message = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "00ff00",
        "summary": "EKS Cluster Deployment",
        "sections":
            [
                {
                    "activityTitle": "Performance Automation - Pipeline Number - {}".format(pipeline_num),
                    "activitySubtitle": "Scenario : {}".format(scenario),
                    "activityImage": "https://teamsnodesample.azurewebsites.net/static/img/image5.png",
                    "facts":
                        [
                            {
                                "name": "Performance Test Scenario {}".format(scenario),
                                "value": "Success"
                            },
                            {
                                "name": "Build Run By",
                                "value": build_user
                            }
                        ],
                    "markdown": True
                }
            ],
        "potentialAction":
            [
                {
                    "@type": "OpenUri",
                    "name": "Bandwidth Stats in Table",
                    "targets":
                        [
                            {
                                "os": "default",
                                "uri": stats_url
                            }
                        ]
                },
                {
                    "@type": "OpenUri",
                    "name": "Bandwidth Stats in Bar Chart",
                    "targets":
                        [
                            {
                                "os": "default",
                                "uri": graph_url
                            }
                        ]
                },
                {
                    "@type": "OpenUri",
                    "name": "View Jenkins Build",
                    "targets":
                        [
                            {
                                "os": "default",
                                "uri": jenkins_url
                            }
                        ]
                }
            ]
    }

    headers = {'content-type': 'application/json'}
    requests.post(webhook, data=json.dumps(message), headers=headers)
    print("Team notification sent successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--scenario', type=str, help="Scenario name to test")
    parser.add_argument('--webhook', type=str, help="Teams Webhook")
    parser.add_argument('--jenkins_url', type=str, help="Jenkins URL")
    parser.add_argument('--build_user', type=str, help="Jenkins build user")
    parser.add_argument('--stats', type=str, help="Html file name")
    parser.add_argument('--graph', type=str, help="Graph file name")
    parser.add_argument('--nexus_url', type=str, help="Nexus URL")
    parser.add_argument('--pipeline_num', type=str, help="Pipeline Number to manage the file")
    args = parser.parse_args()

    stats_file = "{}_{}".format(args.scenario.replace(" ", "_"), args.stats)
    graph_file = "{}_{}".format(args.scenario.replace(" ", "_"), args.graph)
    stats_url = "{}/{}".format(args.nexus_url, stats_file)
    graph_url = "{}/{}".format(args.nexus_url, graph_file)
    team_webhook = "https://trendmicro.webhook.office.com/webhookb2/d6c82240-57b1-41b5-84e8-09def3921052@3e04753a-ae5b-42d4-a86d-d6f05460f9e4/JenkinsCI/b131747740c34e90b770e2a911dea18f/5110c51b-5ae9-4caa-a0a8-aafc778ce125"
    send_teams_notification(team_webhook, args.jenkins_url, args.build_user, args.scenario, stats_url, graph_url,
                            args.pipeline_num)
