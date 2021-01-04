import argparse
import http.client
import json
import os
import ssl
import copy
import time
from urllib import request, error, parse
import uuid
import zeep
from zeep.transports import Transport
from zeep import exceptions
from requests import Session
from glob import glob


class DSMConfig:
	context = ssl._create_unverified_context()
	headers = {
		'Content-Type': 'application/json'
	}

	def __init__(self, dsm_public, dsm_admin_user, dsm_admin_passwd, dsm_port='4119'):
		self.dsm_public = dsm_public
		self.dsm_port = dsm_port
		self.dsm_admin_user = dsm_admin_user
		self.dsm_admin_passwd = dsm_admin_passwd
		self.DSAF_API_KEY_NAME = "MTTR_API_Key"
		self.DSM_BASE_URL = "https://{}:{}".format(dsm_public, dsm_port)
		self.get_cookie()
		self.apiAdminKey = ""

	def get_cookie(self):
		# ================
		# Get cookies
		cookieHeaders = copy.copy(self.headers)
		cookieHeaders["api-version"] = "v1"
		
		data = {
			"userName": self.dsm_admin_user,
			"password": self.dsm_admin_passwd
		}
		json_data = json.dumps(data).encode("utf-8")
		
		req = request.Request('{}/api/sessions'.format(self.DSM_BASE_URL), data=json_data, headers=cookieHeaders)
		authResponse = None
		
		try:
			authResponse = request.urlopen(req, context=self.context)
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			print('Message = ' + str(e.read()))
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
		except http.client.HTTPException as e:
			print('HTTPException: {}'.format(e.message))
		except Exception:
			import traceback
			print('generic exception: ' + traceback.format_exc())
			
		self.rID = json.loads(authResponse.read().decode("utf-8"))["RID"]
		self.cookies = authResponse.info()['Set-Cookie']
		allCookies = self.cookies.split(';')
		for cookie in allCookies:
			if 'sID' in cookie:
				self.sID = cookie.split('=')[1]

	def deleteAPIKey(self, keyname):
		deleteAPIKeyHeaders = copy.copy(self.headers)
		deleteAPIKeyHeaders["api-version"] = "v1"
		deleteAPIKeyHeaders["Cookie"] = self.cookies
		deleteAPIKeyHeaders["rID"] = self.rID
		
		searchCriteria = {
				"searchCriteria": [{
				"fieldName": "keyName",
				"stringTest": "equal",
				"stringValue": keyname
			}]
		}
		searchCriteria_json = json.dumps(searchCriteria).encode("utf-8")
		req = request.Request('{}/api/apikeys/search'.format(self.DSM_BASE_URL), data=searchCriteria_json, headers=deleteAPIKeyHeaders)
		
		try:
			searchResponse = request.urlopen(req, context=self.context)
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			print('Message = ' + str(e.read()))
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
		except http.client.HTTPException as e:
			print('HTTPException: {}'.format(e.message))
		except Exception:
			import traceback
			print('generic exception: ' + traceback.format_exc())
		searchApiKeys = json.loads(searchResponse.read().decode("utf-8"))
		theDeleteKeyID = searchApiKeys["apiKeys"][0]["ID"]
		
		reqDel = request.Request('{}/api/apikeys/{}'.format(self.DSM_BASE_URL, theDeleteKeyID), headers=deleteAPIKeyHeaders, method='DELETE')
		
		try:
			deleteResponse = request.urlopen(reqDel, context=self.context)
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			print('Message = ' + str(e.read()))
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
		except http.client.HTTPException as e:
			print('HTTPException: {}'.format(e.message))
		except Exception:
			import traceback
		return deleteResponse.code

	def deleteCurrentSession(self):
		deleteSessionHeaders = copy.copy(self.headers)
		deleteSessionHeaders["api-version"] = "v1"
		deleteSessionHeaders["Cookie"] = self.cookies
		deleteSessionHeaders["rID"] = self.rID
		
		req = request.Request('{}/api/sessions/current'.format(self.DSM_BASE_URL), headers=deleteSessionHeaders, method='DELETE')
		
		try:
			deleteCurrentResponse = request.urlopen(req, context=self.context)
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			print('Message = ' + str(e.read()))
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
		except http.client.HTTPException as e:
			print('HTTPException: {}'.format(e.message))
		except Exception:
			import traceback
			print('generic exception: ' + traceback.format_exc())
		# print(deleteCurrentResponse.code)
		return deleteCurrentResponse.code

	def createAPIKey(self):
		createAPIKeyHeaders = copy.copy(self.headers)
		createAPIKeyHeaders["api-version"] = "v1"
		createAPIKeyHeaders["Cookie"] = self.cookies
		createAPIKeyHeaders["rID"] = self.rID
		
		dsaf_api_key_data = {
			"keyName": self.DSAF_API_KEY_NAME,
			"description": "API Key for MTTR",
			"roleID": 1
		}
		dsaf_api_key_json = json.dumps(dsaf_api_key_data).encode("utf-8")
		
		apiKeyRequest = request.Request('{}/api/apikeys'.format(self.DSM_BASE_URL), headers=createAPIKeyHeaders, data=dsaf_api_key_json)
		response = None
		try:
			response = request.urlopen(apiKeyRequest, context=self.context)
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			eMessage = str(e.read())
			print('Message = ' + eMessage)
			eMessageJson = json.loads(eMessage)
			if e.code == 400 and "The requested username already exists." in eMessageJson["message"]:
				self.deleteAPIKey(keyname=self.DSAF_API_KEY_NAME)
				self.apiAdminKey = self.createAPIKey()
			if e.code == 401 and "MaxSessionsException occurred when authenticating user [masteradmin]" in e.message:
				print("Seems like we need to wait a bit")
				exit(1)
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
		except http.client.HTTPException as ex:
			print('HTTPException: {}'.format(ex))
		except Exception:
			import traceback
			print('generic exception: ' + traceback.format_exc())
			exit(1)
		self.dsmVersion = response.info()["X-DSM-Version"].split('/')[-1]
		print(self.dsmVersion)
		if not self.apiAdminKey:
			apiAdminKeyJson = json.loads(response.read().decode("utf-8"))
			self.apiAdminKey = apiAdminKeyJson["secretKey"]
		return self.apiAdminKey

	def set_systemSettings(self):
		systemSettingsHeaders = copy.copy(self.headers)
		systemSettingsHeaders["api-version"] = "v1"
		systemSettingsHeaders["api-secret-key"] = self.apiAdminKey
		
		data = {
				"platformSettingActiveSessionsMax": {
				"value": "-1"
			},
				"platformSettingActiveSessionsMaxExceededAction": {
				"value": "2"
			},
				"platformSettingAgentInitiatedActivationEnabled": {
				"value": "For any computers"
			},
				"platformSettingApiSoapWebServiceEnabled": {
				"value": "true"
			}
		}
		sysSettingsData_json = json.dumps(data).encode("utf-8")
		
		req = request.Request('{}/api/systemsettings'.format(self.DSM_BASE_URL), headers=systemSettingsHeaders, data=sysSettingsData_json)
		try:
			setSettingsResponse = request.urlopen(req, context=self.context)
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			print('Message = ' + str(e.read()))
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
		except http.client.HTTPException as e:
			print('HTTPException: {}'.format(e))
		except Exception:
			import traceback
			print('generic exception: {}'.format(traceback.format_exc()))
			
		return setSettingsResponse.code

	def uploadPackage(self, filePath):
		wsdl = '{}/webservice/Manager?WSDL'.format(self.DSM_BASE_URL)
		
		session = Session()
		session.verify = False
		transport = Transport(session=session)
		
		client = zeep.Client(wsdl=wsdl, transport=transport)
		try:
			with open(filePath, "rb") as f_in:
				print(os.path.basename(f_in.name))
				uploadResp = client.service.softwareStore(software=f_in.read(), fileName=os.path.basename(f_in.name), notes=os.path.basename(f_in.name), sID=self.sID)
		except zeep.exceptions.Fault as zeepErr:
			if "The selected software name already exists" in zeepErr.message:
				print(zeepErr.message)
				return
			else:
				print(zeepErr.message)
				exit(1)
		print(uploadResp)
		
		#self.deleteAPIKey(keyname=self.DSAF_API_KEY_NAME)
		return uploadResp

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Optional app description')
	parser.add_argument('--dsmHost', type=str, help="DSM publick host")
	parser.add_argument('--dsmUser', type=str, help="DSM admin user")
	parser.add_argument('--dsmPasswd', type=str, help="DSM admin password")
	parser.add_argument('--agentFolder', type=str, help="Path to folder where Deep Security Agent is stored")
	args = parser.parse_args()
	
	searchString = args.agentFolder+'/Agent*.zip'
	agentFile = glob(searchString)

	dsmAPIinstance = DSMConfig(args.dsmHost, dsm_admin_user=args.dsmUser, dsm_admin_passwd=args.dsmPasswd)
	dsmAPIinstance.createAPIKey()

	for i in agentFile:
                strAgentFile = str(i)
                print(strAgentFile)
                dsmAPIinstance.uploadPackage(strAgentFile)
                time.sleep(5)

	#dsmAPIinstance.deleteCurrentSession()
