# Anarcho-Tech NYC: Tor

An [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) for building a [Tor](https://torproject.org/) server from source. Notably, this role has been tested with [Raspbian](https://www.raspbian.org/) on [Raspberry Pi](https://www.raspberrypi.org/) hardware. Its purpose is to make it simple to install a Tor server that can be configured as an [Onion service server](https://www.torproject.org/docs/onion-services).

## Configuring Onion services

Of this role's [default variables](defaults/main.yml), which you can override using any of [Ansible's variable precedence rules](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable), the most important is the `onion_services` list. It describes the Onion service configuations you want implemented. Each item in the list is a dictionary with the following keys:

* `name`: Name of [the Onion service directory](https://www.torproject.org/docs/tor-manual.html#HiddenServiceDir).
* `state`: Whether the Onion service's configuration should be `present`, in which case its configuration file will be written, or `absent` in which case the service's associated configuration file will be removed from the managed host.
* `enabled`: Whether the Onion service should be active on the managed host. Valid values are either `link` (the default), in which case the Onion service will be enabled (i.e., symlinked to the `onions-enabled` directory), or `absent`, in which case the symlink will be removed.
* `version`: [Rendezvous ("Onion") service descriptor version number](https://www.torproject.org/docs/tor-manual.html#HiddenServiceVersion).
* `virtports`: List of [the Onion service's open virtual ports](https://www.torproject.org/docs/tor-manual.html#HiddenServicePort). An item in the `virtports` list is itself a dictionary with the following keys:
    * `port_number`: TCP port number to expose on the "public" Onion side. This is required; a virtual port must have a port number.
    * `unix_socket`: If the [Torified](https://trac.torproject.org/projects/tor/wiki/doc/TorifyHOWTO#Terminology) service communicates via a UNIX domain socket, this specifies the path to its socket file.
    * `target_addr`: The IPv4 or IPv6 address of the Torified service, if the service listens for incoming connections on an internet socket. Defaults to `127.0.0.1` if neither this key nor `unix_socket` are defined.
    * `target_port`: TCP port number of the exposed service. Defaults to `port_number` unless `unix_socket` is defined.
* `auth_type`: Type of [Onion service authentication](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) to use with which to authorize incoming client connections. This can be either `stealth`, `basic`, or `false` (which is the default if left undefined).
* `clients`: List of [client names](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) to authorize. This key is ignored unless `auth_type` is set to a value other than `false`.

It may be helpful to see a few examples.

1. Simple SSH Onion service providing access to the Onion service host via SSH-over-Tor:
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
    This is equivalent to `HiddenServicePort 22 127.0.0.1:22`.
1. Authenticated stealth Onion service for a Dark Web site serving two Tor clients with the exposed HTTP server running on an alternate port on `localhost`:
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
    With this configuration, `alice` and `bob` must [write `HidServAuth` lines in their local `torrc` files](https://github.com/AnarchoTechNYC/meta/wiki/Connecting-to-an-authenticated-Onion-service), but will then be able to enter an Onion address, e.g., `http://abcdef0123456789.onion/` in Tor Browser (connecting to the Onion's virtual port 80) to access the service listening on the Onion's real port `8080`.
1. Multiple Onions on one server. One of the Onions has two open virtual ports. The SSH management port is available only over a `basic` authenticated Tor connection, and one of the Web servers are available over a UNIX domain socket in order to mitigate [localhost bypass attacks](https://github.com/AnarchoTechNYC/CTF/wiki/Tor#localhost-bypass-attack):
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
    ```yml
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
    This configuration will route each new incoming connection to the Onion's virtual port `443` to a random target address in the range `192.168.1.10-12:443`. With such a configuration, be certain to carefully ensure that data transported between the Onion service host and the machine at `192.168.1.10` through `192.168.1.12` is encrypted while in motion.

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

## Maintaining Tor

Merely Installing Tor is not sufficient for hosts where [NetSec](https://github.com/AnarchoTechNYC/meta/wiki/NetSec) considerations are critical. The installed version of Tor must be kept up-to-date in order to apply security patches. This Ansible role therefore compares the installed version of the system Tor against the latest source release provided by the Tor Project and will rebuild Tor from source whenever a new version is released. This happens *every* time an Ansible play that includes this role is run.

Building Tor from source can take a significant amount of time on extremely low-power hardware. (It takes ~1 hour on a Raspberry Pi model 1.) Since this can be a concern in its own right, these tasks are tagged `tor-build` and can be skipped by invoking `ansible` or `ansible-playbook` with the `--skip-tags tor-build` command-line option. See the [Task tags](#task-tags) section for more details.


## Task tags

> :construction:

The following tags are provided by this role:

* `tor-build` - Tasks that build Tor from source.
