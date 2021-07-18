from __future__ import (absolute_import, division, print_function)

from ansible.utils.display import Display
from ansible.plugins.lookup import LookupBase
from ansible.errors import AnsibleError

from ansible_collections.isometry.terraform.plugins.module_utils.terraform import TfeApi

__metaclass__ = type

DOCUMENTATION = r"""
lookup: isometry.terraform.output
author: Robin Breathe <robin@isometry.net>
short_description: read terraform outputs
description:
  - Lookup Terraform outputs from either a local Terraform module or direct from Terraform Cloud/Enterprise
options:
  _terms:
    description:
      - Terraform outputs to return
      - Returns all outputs if unspecified
    required: False
  path:
    description:
      - Path to local Terraform module
      - Required for retrieval of outputs from a local Terraform module
    type: string
    vars:
      - name: ansible_lookup_terraform_path
    env:
      - name: ANSIBLE_LOOKUP_TERRAFORM_PATH
    ini:
        - section: terraform_lookup
          key: path
  server:
    description: Terraform Cloud/Enterprise server
    type: string
    default: https://app.terraform.io
    vars:
      - name: ansible_lookup_terraform_server
    env:
      - name: ANSIBLE_LOOKUP_TERRAFORM_SERVER
      - name: TF_SERVER
    ini:
      - section: terraform_lookup
        key: server
  token:
    description:
      - Terraform Cloud/Enterprise API token
      - Supports [terraform-credentials-env](https://github.com/apparentlymart/terraform-credentials-env)-compatible environment variable
      - Supports automatic fallback to keyring item (e.g. `app.terraform.io token`)
    type: string
    vars:
      - name: ansible_lookup_terraform_token
    env:
      - name: ANSIBLE_LOOKUP_TERRAFORM_TOKEN
      - name: TF_TOKEN
    ini:
      - section: terraform_lookup
        key: token
  organization:
    description: Organization
    type: string
    vars:
      - name: ansible_lookup_terraform_organization
    env:
      - name: ANSIBLE_LOOKUP_TERRAFORM_ORGANIZATION
      - name: TF_ORGANIZATION
    ini:
      - section: terraform_lookup
        key: organization
  workspace:
    description: Workspace
    type: string
    vars:
      - name: ansible_lookup_terraform_workspace
    env:
      - name: ANSIBLE_LOOKUP_TERRAFORM_WORKSPACE
      - name: TF_WORKSPACE
    ini:
      - section: terraform_lookup
        key: workspace
  cooked:
    description: Strip type and sensitivity attributes, returning simple key-value output
    type: boolean
    default: True
    vars:
      - name: ansible_lookup_terraform_cooked
    env:
      - name: ANSIBLE_LOOKUP_TERRAFORM_COOKED
      - name: TF_COOKED
    ini:
      - section: terraform_lookup
        key: cooked
"""

EXAMPLES = """
- name: retrieve all outputs from our-workspace in my-org
  debug:
    msg: "{{ lookup('isometry.terraform.output', organization='my-org', workspace='our-workspace') }}"

- name: retrieve all outputs from local terraform module my-module
  debug:
    msg: "{{ lookup('isometry.terraform.output', path='my-module') }}"

- name: set server_address fact from terraform
  set_fact:
    server_address: "{{ lookup('isometry.terraform.output', 'server_address', organization='my-org', workspace='our-workspace') }}"

- name: loop over servers
  debug:
    var: item
  loop: "{{ lookup('isometry.terraform.output', 'servers', path='my-module') | dict2items }}"

- name: cache terraform output in terraform_output fact
  set_fact:
    cacheable: yes
    terraform_output: "{{ lookup('isometry.terraform.output', organization='my-org', workspace='our-workspace') }}"

- name: transform all terraform outputs into ansible facts
  set_fact:
    "{{ item.key }}": "{{ item.value }}"
  loop: "{{ lookup('isometry.terraform.output', path='my-module') }}"
"""

RETURN = """
  _list:
    description:
      - terraform output object
    type: list
    elements: dict
"""

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables, **kwargs):

        self.set_options(var_options=variables, direct=kwargs)

        path = self.get_option('path')
        server = self.get_option("server")
        token = self.get_option("token")
        organization = self.get_option("organization")
        workspace = self.get_option("workspace")
        cooked = self.get_option("cooked")

        outputs = {}

        if path is not None:
            from subprocess import run
            from json import loads

            display.vvv("terraform lookup: %s %s" % (path, terms))

            terraform_output_cmd = ["terraform", "output", "-no-color", "-json"]
            p = run(terraform_output_cmd, cwd=path, capture_output=True, encoding="utf-8")

            if p.returncode != 0:
                raise AnsibleError("lookup_plugin.terraform(path='%s') returned %d: %s" % (path, p.returncode, p.stderr))

            outputs = loads(p.stdout)

        else:
            if organization is None or workspace is None:
                raise AnsibleError("lookup_plugin.terraform: organization and workspace must be specified")

            display.vvv("tfe lookup: %s/%s/%s %s" % (server, organization, workspace, terms))

            tfe = TfeApi(server=server, token=token)

            outputs = tfe.workspace_outputs(organization, workspace)

        if len(terms) == 0:
            if cooked:
                return [{k: v['value'] for k, v in outputs.items()}]
            else:
                return [outputs]
        else:
            return [outputs.get(term, {}).get('value') for term in terms]
