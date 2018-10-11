# Anarcho-Tech NYC: Tor

An [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) for building a [Tor](https://torproject.org/) server from source. Notably, this role has been tested with [Raspbian](https://www.raspbian.org/) on [Raspberry Pi](https://www.raspberrypi.org/) hardware. Its purpose is to make it simple to install a Tor server that can be configured as an [Onion service server](https://www.torproject.org/docs/onion-services).

# Configuring Onion services

This role provides [default variables](defaults/main.yml), which you can override using any of [Ansible's variable precedence rules](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable). Of these, the most important is the `onion_services` list. It describes the Onion service configuations you want to deploy. Each item in the list is a dictionary with the following keys:

* `name`: Name of [the Onion service directory](https://www.torproject.org/docs/tor-manual.html#HiddenServiceDir).
* `state`: Either `present`, in which case the Onion service configuration file will be available, or `absent` in which case it will not.
* `enabled`: Can be either `link` (the default), in which case the Onion service will be enabled, or `absent`, in which case the Onion service configuration will be disabled.
* `version`: [Rendezvous service descriptor version number](https://www.torproject.org/docs/tor-manual.html#HiddenServiceVersion).
* `virtports`: List of [virtual ports of the Onion service](https://www.torproject.org/docs/tor-manual.html#HiddenServicePort). An item in the `virtports` list may have:
    * `port_number`: TCP port number to expose on the "public" Onion side.
    * `unix_socket`: Path to socket file for the exposed service.
    * `target_addr`: Target IPv4 or IPv6 address of the exposed service.
    * `target_port`: TCP port number of the exposed service.
* `auth_type`: Type of [Onion service authentication](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) to use with which to authorize incoming client connections.
* `clients`: List of [client names](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) to authorize.

It may be helpful to see a few examples.

1. Simple SSH onion service:
    ```yml
    onion_services:
      - name: my-onion
        virtports:
          - port_number: 22
    ```
    The above will create an Onion service configuration in the file `/etc/tor/torrc.d/onions-enabled/my-onion` with the following contents:
    ```
    HiddenServiceDir /var/lib/tor/onion-services/my-onion
    HiddenServicePort 22
    HiddenServiceVersion 2
    ```
1. Authenticated stealth Onion service for a Dark Web site serving two Tor clients with HTTP server running on an alternate port:
    ```yml
    onion_services:
      - name: dark-website
        virtports:
          - port_number: 80
            target_port: 8080
        auth_type: stealth
        clients:
          - alice
          - bob
    ```
    The above will create an Onion service configuration in the file `/etc/tor/torrc.d/onions-enabled/dark-website` with the following contents:
    ```
    HiddenServiceDir /var/lib/tor/onion-services/dark-website
    HiddenServicePort 80 127.0.0.1:8080
    HiddenServiceVersion 2
    HiddenServiceAuthorizeClient stealth alice,bob
    ```
1. Multiple Onions, one with multiple open ports. The SSH management port is available only over `basic` authenticated Tor connection, and one of the Web servers are available over a UNIX domain socket to reduce [localhost bypass attacks](https://github.com/AnarchoTechNYC/CTF/wiki/Tor#localhost-bypass-attack):
    ```yml
    onion_services:
      - name: onion-ssh
        virtports:
          - port_number: 22
        auth_type: basic
        clients:
          - admin
      - name: onion-web
          - port_number: 80
          - port_number: 8080
            unix_socket: /etc/lighttpd/unix.sock
    ```
    The above will create two Onion service configuration files. In file `/etc/tor/torrc.d/onions-enabled/onion-ssh`:
    ```
    HiddenServiceDir /var/lib/tor/onion-services/onion-jumpbox
    HiddenServicePort 22
    HiddenServiceVersion 2
    HiddenServiceAuthorizeClient basic admin
    ```
    Meanwhile, in `/etc/tor/torrc.d/onions-enabled/onion-web`:
    ```
    HiddenServiceDir /var/lib/tor/onion-services/onion-web
    HiddenServicePort 80
    HiddenServicePort 8080 unix:/etc/lighttpd/unix.sock
    HiddenServiceVersion 2
    ```
1. Single next-generation Onion site, randomly balancing across three Web app servers:
    ```
    onion_services:
      - name: onion-high-availability-web
        version: 3
        virtports:
          - port_number: 443
            target_addr: 192.168.1.10
          - port_number: 443
            target_addr: 192.168.1.11
          - port_number: 443
            target_addr: 192.168.1.12
    ```
    The above will create an Onion service configuration file in the file `/etc/tor/torrc.d/onions-enabled/onion-high-availability-web` with the following contents:
    ```
    HiddenServiceDir /var/lib/tor/onion-services/onion-high-availability-web
    HiddenServicePort 443 192.168.1.10
    HiddenServicePort 443 192.168.1.11
    HiddenServicePort 443 192.168.1.12
    HiddenServiceVersion 3
    ```

Onion service configurations are stored in `/etc/tor/torrc.d/onions-available`, which is `%include`'ed via the main Tor configuration file, `/etc/tor/torrc`. To enable an available configuration, symlink the file for the appropriate Onion service to the `/etc/tor/torrc.d/onions-enabled` directory and reload the Tor service (by sending the main Tor process a `HUP` signal). To disable an Onion, unlink the file from the `onions-enabled` directory and reload the Tor service again.

The symlinks are handled by the `enabled` key, described above, so you can do something like the following to disable but not remove an Onion service configuration:

```yml
onion_services:
  - name: my-service
    enabled: absent
    virtports:
      - port_number: 80
```

With such a configuration, the `/etc/tor/torrc.d/onions-available/my-service` file will exist, but it will not be symlinked from `/etc/tor/torrc.d/onions-enabled/my-service`.

You can also ensure that any given Onion service configurations, along with its private (and client) keys, are wiped from the expected places on disk:

```yml
onion_services:
  - name: my-service
    state: absent
```

The above will ensure that the `/etc/tor/torrc.d/onions-available/my-service` file and the `/var/lib/tor/onion-services/my-service` directory hierarchy will be deleted. Note that since a completely missing configuration cannot be enabled, if you specify `state: absent`, the value of `enabled` is ignored (i.e., always skipped).
