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
from zeep.exceptions import Fault
from requests import Session
from requests.exceptions import ConnectionError, Timeout
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
		self.rID = None  
		self.cookies = None  
		self.sID = None
		self.get_cookie()
		self.apiAdminKey = ""
		self.wsdl = '{}/webservice/Manager?WSDL'.format(self.DSM_BASE_URL)
		self.session = Session()
		self.session.verify = False
		self.transport = Transport(session=self.session)
		self.client = zeep.Client(wsdl=self.wsdl, transport=self.transport)
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
		
		if authResponse:
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
		keyname = self.DSAF_API_KEY_NAME
		
		searchCriteria = {
				"searchCriteria": [{
				"fieldName": "keyName",
				"stringTest": "equal",
				"stringValue": keyname
			}]
		}
		searchCriteria_json = json.dumps(searchCriteria).encode("utf-8")
		req = request.Request('{}/api/apikeys/search'.format(self.DSM_BASE_URL), data=searchCriteria_json, headers=deleteAPIKeyHeaders)
		
		searchResponse = None
		
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
		
		deleteCurrentResponse = None
		try:
			deleteCurrentResponse = request.urlopen(req, context=self.context)
			print(f"deleteCurrentResponse.code: {deleteCurrentResponse.code}")
			return deleteCurrentResponse.code
		except error.HTTPError as e:
			print('HTTPError = ' + str(e.code))
			print('Message = ' + str(e.read()))
			return e.code
		except error.URLError as e:
			print('URLError = ' + str(e.reason))
			return None
		except http.client.HTTPException as e:
			print('HTTPException: {}'.format(e.message))
			return None
		except Exception:
			import traceback
			print('generic exception: ' + traceback.format_exc())
			return None

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
			if e.code == 401 and "MaxSessionsException occurred when authenticating user [supermasteradmin]" in e.message:
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
		uploadResp = None
		try:
			with open(filePath, "rb") as f_in:
				file_name = os.path.basename(f_in.name)
				print(f"Uploading file: {file_name}")
				uploadResp = self.client.service.softwareStore(
					software=f_in.read(),
					fileName=file_name,
					notes=file_name,
					sID=self.sID
				)
		except FileNotFoundError:
			print(f"File not found: {filePath}")
			return
		except IOError as io_err:
			print(f"IO error occurred: {io_err}")
			return
		except Fault as zeepErr:
			if "The selected software name already exists" in zeepErr.message:
				print(f"Warning: {zeepErr.message}")
				return
			else:
				print(f"Error: {zeepErr.message}")
				exit(1)
		except Exception as err:
			print(f"An unexpected error occurred: {err}")
			exit(1)
		else:
			print("Upload response: %s", uploadResp)
			print(uploadResp)
			self.deleteAPIKey(keyname=self.DSAF_API_KEY_NAME)
			return uploadResp
		finally:
			self.client.transport.session.close()


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
		# Upload with simple retry to avoid unnecessary delays
		max_retries = 3
		for attempt in range(1, max_retries + 1):
			try:
				dsmAPIinstance.uploadPackage(strAgentFile)
				break
			except Exception as e:
				print(f"Upload attempt {attempt} failed for {strAgentFile}: {e}")
				if attempt == max_retries:
					raise

	dsmAPIinstance.deleteCurrentSession()
	#dsmAPIinstance.deleteAPIKey(keyname=None)