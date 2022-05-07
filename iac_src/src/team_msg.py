import argparse
import requests
import json


def send_teams_notification(webhook, jenkins_url, build_user, scenario, stats_url, graph_url, manifest_file_url,
                            pipeline_num):
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
                    "name": "Infra Access Detail",
                    "targets":
                        [
                            {
                                "os": "default",
                                "uri": manifest_file_url
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
    parser.add_argument('--manifest_file', type=str, help="Manifest file contains cloud infra access detail")
    parser.add_argument('--nexus_url', type=str, help="Nexus URL")
    parser.add_argument('--pipeline_num', type=str, help="Pipeline Number to manage the file")
    args = parser.parse_args()

    stats_file = "{}_{}".format(args.scenario.replace(" ", "_"), args.stats)
    graph_file = "{}_{}".format(args.scenario.replace(" ", "_"), args.graph)
    stats_url = "{}/{}".format(args.nexus_url, stats_file)
    graph_url = "{}/{}".format(args.nexus_url, graph_file)
    manifest_file_url = "{}/{}".format(args.nexus_url, args.manifest_file)
    send_teams_notification(args.webhook, args.jenkins_url, args.build_user, args.scenario, stats_url, graph_url,
                            manifest_file_url, args.pipeline_num)
