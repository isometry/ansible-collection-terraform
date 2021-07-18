from __future__ import (absolute_import, division, print_function)

from ansible.errors import AnsibleError

from functools import cache
from requests import Session
from requests.auth import AuthBase


class TfeAuth(AuthBase):
    """Attaches Terraform Cloud Token Authentication to the given Request object."""

    def __init__(self, server="https://app.terraform.io", token=None):
        if token is None:
            # look for terraform-credentials-env compatible token
            from urllib.parse import urlsplit
            from os import environ
            hostname = urlsplit(server).hostname
            token = environ.get("TF_TOKEN_%s" % (hostname.replace('.', '_')))
        if token is None:
            try:
                from keyring import get_password
                token = get_password(hostname, 'token')
            except ImportError:
                pass
        if token is None:
            raise AnsibleError("API token must be specified for TFE lookup")

        self.token = token

    def __call__(self, r):
        r.headers["Authorization"] = "Bearer %s" % (self.token)
        return r


class TfeApi:
    def __init__(self, server="https://app.terraform.io", token=None):
        self.session = Session()
        self.session.auth = TfeAuth(server, token)
        self.session.headers.update({"Content-Type": "application/vnd.api+json"})

        self.apibase = "%s/api/v2" % (server)

    def get(self, endpoint, params=None):
        return self.session.get("%s/%s" % (self.apibase, endpoint), params=params).json()
    read = get

    @cache
    def workspace_by_name(self, organization, workspace):
        return self.get("organizations/%s/workspaces/%s" % (organization, workspace))

    @cache
    def output_by_id(self, id):
        result = self.get("state-version-outputs/%s" % (id))
        return result.get('data', {}).get('attributes', {})

    @cache
    def workspace_outputs(self, organization, workspace):
        workspace_metadata = self.workspace_by_name(organization, workspace)
        output_list = workspace_metadata.get('data', {}).get('relationships', {}).get('outputs', {}).get('data', [])
        outputs = {}
        for output in output_list:
            output_data = self.output_by_id(output['id'])
            outputs[output_data['name']] = {k: v for k, v in output_data.items() if k != 'name'}
        return outputs
