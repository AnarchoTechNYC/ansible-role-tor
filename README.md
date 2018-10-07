# Anarcho-Tech NYC: Tor

An [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) for building a [Tor](https://torproject.org/) server from source. Notably, this role has been tested with [Raspbian](https://www.raspbian.org/) on [Raspberry Pi](https://www.raspberrypi.org/) hardware. Its purpose is to make it simple to install a Tor server that can be used as an [Onion service server](https://www.torproject.org/docs/onion-services).

# Configuring Onion services

This role provides [default variables](defaults/main.yml), which you can override using any of [Ansible's variable precedence rules](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable). Of these, the most important is the `onion_services` dictionary. It describes the Onion service configuations you want to deploy and is composed of the following structure:

* `onion_services`
    * *key name*
        * `name`: Name of [the Onion service directory](https://www.torproject.org/docs/tor-manual.html#HiddenServiceDir).
        * `version`: [Rendezvous service descriptor version number](https://www.torproject.org/docs/tor-manual.html#HiddenServiceVersion).
        * `virtport`: [Virtual port of the Onion service](https://www.torproject.org/docs/tor-manual.html#HiddenServicePort).
        * `target_addr`: [Address of the target service](https://www.torproject.org/docs/tor-manual.html#HiddenServicePort).
        * `target_port`: [TCP port number of the target service](https://www.torproject.org/docs/tor-manual.html#HiddenServicePort).
        * `auth_type`: Type of [Onion service authentication](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) to use with which to authorize incoming client connections.
        * `clients`: List of [client names](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) to authorize.
