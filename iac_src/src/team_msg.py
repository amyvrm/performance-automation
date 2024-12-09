import argparse
import requests
import json

def send_teams_notification(webhook, build_url, build_user, scenario, stats_url, graph_url, manifest_file_url,
                            pipeline_num):
    status_color = "red"
    if "SUCCESS" in status or "PASSED" in status:
        status_color="green"
    text = "<b>Job: </b><span style='font-size: 20px; font-weight: bold;'>{},</span> <span style='font-size: 16px; font-weight: bold;'><a href='{}'> build: {}</a></span><br>".format(pipeline_name, build_url, build_number)
    text += "<b>Status:</b>  <b style=\"color: {};\">{}</b>".format(status_color,status)
    if "FAILED" in status or "FAILURE" in status:
        text += " (see <a href='{}console'>Console Logs</a>)".format(build_url)
    text += "<br><b>Run by</b>: {}<br>".format(user)

    if "SUCCESS" in status or "PASSED" in status:
        # Results load 
        text += "<br>Test scenario: <b>{}</b>&nbsp;&nbsp;{}".format(scenario)
        text += "<hr>"
        text += "<b><a href={} style='background-color: #c0c0c0; color: black; font-weight: bold; font-size: 16px; padding: 10px 20px; border: 2px solid white; border-radius: 15px; text-align: center; text-decoration: none; display: inline-block;'>&nbsp;&nbsp;Bandwidth Stats in Table&nbsp;&nbsp;</a></b>".format(stats_url)   
        text += "&nbsp;&nbsp;&nbsp;&nbsp;<b><a href={} style='background-color: #c0c0c0; color: black; font-weight: bold; font-size: 16px; padding: 10px 20px; border: 2px solid white; border-radius: 15px; text-align: center; text-decoration: none; display: inline-block;'>&nbsp;&nbsp;Bandwidth Stats in Bar Chart&nbsp;&nbsp;</a></b>".format(graph_url)   
        text += "&nbsp;&nbsp;&nbsp;&nbsp;<b><a href={} style='background-color: #c0c0c0; color: black; font-weight: bold; font-size: 16px; padding: 10px 20px; border: 2px solid white; border-radius: 15px; text-align: center; text-decoration: none; display: inline-block;'>&nbsp;&nbsp;Infra Access Detail&nbsp;&nbsp;</a></b>".format(manifest_file_url)   
        text += "&nbsp;&nbsp;&nbsp;&nbsp;<b><a href={} style='background-color: #c0c0c0; color: black; font-weight: bold; font-size: 16px; padding: 10px 20px; border: 2px solid white; border-radius: 15px; text-align: center; text-decoration: none; display: inline-block;'>&nbsp;&nbsp;View Jenkins Build&nbsp;&nbsp;</a></b>".format(build_url)   
      message = {"text": text}
      
    message2 = {
        "@type": "AdaptiveCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "00ff00",
        "summary": "EKS Cluster Deployment",
        "sections": [
            {
                "activityTitle": "Performance Automation - Pipeline Number - {}".format(pipeline_num),
                "activitySubtitle": "Scenario : {}".format(scenario),
                "activityImage": "https://teamsnodesample.azurewebsites.net/static/img/image5.png",
                "facts": [
                    {"name": "Performance Test Scenario {}".format(scenario), "value": "Success"},
                    {"name": "Build Run By", "value": build_user}
                ],
                "markdown": "True"
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "Bandwidth Stats in Table",
                "targets": [{"os": "default", "uri": stats_url}]
            },
            {
                "@type": "OpenUri",
                "name": "Bandwidth Stats in Bar Chart",
                "targets": [{"os": "default", "uri": graph_url}]
            },
            {
                "@type": "OpenUri",
                "name": "Infra Access Detail",
                "targets": [{"os": "default", "uri": manifest_file_url}]
            },
            {
                "@type": "OpenUri",
                "name": "View Jenkins Build",
                "targets": [{"os": "default", "uri": jenkins_url}]
            }
        ]
    }  */

    headers = {'Content-Type': 'application/json'}
    try:
        #print(json.dumps(message, indent=2))
        response = requests.post(webhook, data=json.dumps(message), headers=headers)
        response.raise_for_status()
        print("Team notification sent successfully")
    except requests.exceptions.RequestException as e:
        print(f"Failed to send notification: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Please give argument to perform operations')
    parser.add_argument('--scenario', type=str, help="Scenario name to test")
    parser.add_argument('--webhook', type=str, help="Teams Webhook")
    parser.add_argument('--jenkins_url', type=str, help="Jenkins URL")
    parser.add_argument('--build_user', type=str, help="Jenkins build user")
    parser.add_argument('--stats', type=str, help="Html file name")
    parser.add_argument('--graph', type=str, help="Graph file name")
    parser.add_argument('--manifest_file', type=str, help="Manifest file contains cloud infra access detail")
    parser.add_argument('--jfrog_url', type=str, help="JFrog URL")
    parser.add_argument('--pipeline_num', type=str, help="Pipeline Number to manage the file")
    args = parser.parse_args()

    stats_file = "{}_{}".format(args.scenario.replace(" ", "_"), args.stats)
    graph_file = "{}_{}".format(args.scenario.replace(" ", "_"), args.graph)
    stats_url = "{}/{}".format(args.jfrog_url, stats_file)
    graph_url = "{}/{}".format(args.jfrog_url, graph_file)
    manifest_file_url = "{}/{}".format(args.jfrog_url, args.manifest_file)
    send_teams_notification(args.webhook, args.jenkins_url, args.build_user, args.scenario, stats_url, graph_url,
                            manifest_file_url, args.pipeline_num)
