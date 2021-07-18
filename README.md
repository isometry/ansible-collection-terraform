# Ansible Collection Terraform

Read [Terraform](https://www.terraform.io/) outputs for use in Ansible.

## Features 

* Supports direct retrieval from Terraform Cloud/Enterprise.
* Supports arbitrary local modules with any backend configuration.
* Retrieve all outputs or just a specified subset.

## Installation

```sh
ansible-galaxy collection install isometry.terraform
```

## Configuration

### Local Terraform Module

To retrieve outputs from a local module available via filesystem path, just the `path` to the module is required.

A version of `terraform` binary compatible with the targeted module must also be executable within `PATH`.

### Terraform Cloud

To retrieve outputs from a Terraform Cloud workspace, the relevant `organization`, `workspace` and an API `token` must be configured. These may be:

* specified as key-value arguments to the lookup (e.g. `lookup('isometry.terraform.output', organization='my-org', workspace='my-workspace', token='my-token')`);
* set as variables with the `ansible_lookup_terraform_` prefix (i.e. `ansible_lookup_terraform_organization`/`ansible_lookup_terraform_workspace`/`ansible_lookup_terraform_token`);
* specified via the environment with either the `ANSIBLE_LOOKUP_TERRAFORM_` or `TF_` prefix (i.e. `TF_ORGANIZATION`/`TF_WORKSPACE`/`TF_TOKEN`);
  * The `token` may also be specified in a [terraform-credentials-env](https://github.com/apparentlymart/terraform-credentials-env)-compatible environment variable (e.g. `TF_TOKEN_app_terraform_io` for Terraform Cloud) for simplified use in automation.
* set within the `[terraform_lookup]` section of `ansible.cfg`.

### Terraform Enterprise

Interaction with Terraform Enterprise is untested, but in theory has the same requirements as Terraform Cloud, in addition to which the `address` must be configured.

## Example Usage

```yaml
- name: retrieve all outputs from our-workspace in my-org
  debug:
    msg: "{{ lookup('isometry.terraform.output', organization='my-org', workspace='our-workspace') }}"

- name: retrieve all outputs from local terraform module my-module
  debug:
    msg: "{{ lookup('isometry.terraform.output', path='my-module') }}"

- name: set server_address fact from terraform
  set_fact:
    server_address: "{{ lookup('isometry.terraform.output', 'server_address', organization='my-org', workspace='our-workspace') }}"

- name: dump items in servers output map
  debug:
    var: item
  loop: "{{ lookup('isometry.terraform.output', 'servers', path='my-module') | dict2items }}"

- name: cache terraform output in terraform_output fact
  set_fact:
    cacheable: yes
    terraform_output: "{{ lookup('isometry.terraform.output', organization='my-org', workspace='our-workspace') }}"

- name: transform all terraform outputs from my-module into ansible facts
  set_fact:
    "{{ item.key }}": "{{ item.value }}"
  loop: "{{ lookup('isometry.terraform.output', path='my-module') }}"
```
