# Anarcho-Tech NYC: Tor [![Build Status](https://travis-ci.org/AnarchoTechNYC/ansible-role-tor.svg?branch=master)](https://travis-ci.org/AnarchoTechNYC/ansible-role-tor)

An [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html) for building a [Tor](https://torproject.org/) server from source. Notably, this role has been tested with [Raspbian](https://www.raspbian.org/) on [Raspberry Pi](https://www.raspberrypi.org/) hardware and supports the [Vanguards](https://github.com/mikeperry-tor/vanguards) high-security Onion service Tor controller add-on script. This role's purpose is to make it simple to install a system Tor that can be configured as a high-security [Onion service server](https://www.torproject.org/docs/onion-services).

## Configuring Onion services

> :beginner: "Onion services" were formerly known as "(Location) Hidden Services" and are sometimes still referred to by that name.

Onion services is the generic name for network-capable services exposed over Tor. For example, a Dark Web site is "just" an HTTP server ([Nginx](https://www.nginx.com/), [Apache HTTPD](https://httpd.apache.org/), [Lighttpd](https://www.lighttpd.net/), [Caddy](https://caddyserver.com/), etc.) with a Tor server in front of it. A given Tor installation can function as a server or a client:

* As a server, a Tor instance can accept inbound connections on virtual Onion ports received from the Tor network and route them to a "real" service either via IP address or UNIX domain socket. In this situation, the Tor instance is called an Onion service server.
* As a client, a Tor instance can make connections to an Onion service on behalf of a userland application, such as a Web browser. This is how Tor Browser is able to connect to `.onion` domains. In this situation, the Tor instance is called an Onion service client.

This Ansible role can be used to configure a system Tor installation as a server, a client, or both.

### Onion service server configuration variables

Of this role's [default variables](defaults/main.yaml), which you can override using any of [Ansible's variable precedence rules](https://docs.ansible.com/ansible/latest/user_guide/playbooks_variables.html#variable-precedence-where-should-i-put-a-variable), one of the most important is the `onion_services` list. It describes the Onion service configuations you want implemented. Each item in the list is a dictionary with the following keys:

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
* `private_key_file`: Path to a specific `private_key` file to use for this Onion service. You should almost certainly [ensure this file is encrypted with Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/playbooks_vault.html#single-encrypted-variable).
* `client_keys_file`: Path to a specific `client_keys` file to use for this Onion service. You should almost certainly [ensure this variable is encrypted with Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/playbooks_vault.html#single-encrypted-variable).

It may be helpful to see a few examples.

1. Simple SSH Onion service providing access to the Onion service host via SSH-over-Tor:
    ```yaml
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
    ```yaml
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
    ```yaml
    onion_services:
      - name: onion-ssh
        virtports:
          - port_number: 22
        auth_type: basic
        clients:
          - admin
      - name: onion-web
        virtports:
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
    ```yaml
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

#### Overriding Onion service configurations

In addition to the `onion_services` list, you can override specific Onion service configuration keys for a given Onion service configuration using the `onion_services_overrides` list. This list has the same [structure as the `onion_services` list](#onion-service-server-configuration-variables) but is intended to be placed in a higher-precedence load order (such as a group- or host-specific inventory file) or to be constructed dynamically during runtime. It can be used to, for example, define per-host Onion service ports:

```yaml
# In `group_vars/all.yaml` file.
---
onion_services:
  - name: onion-ssh
    virtports:
      - port_number: 22
    auth_type: stealth
    clients:
      - admin
```

```yaml
# In `host_vars/jumpbox1.example.com.yaml` file.
---
onion_services_overrides:
  - name: onion-ssh
    virtports:
      - port_number: 39741
        target_port: 22
```

```yaml
# In `host_vars/jumpbox2.example.com.yaml` file.
---
onion_services_overrides:
  - name: onion-ssh
    virtports:
      - port_number: 12946
        target_port: 22
```

The above will cause the `onion-ssh` service on `jumpbox1.example.com` to be exposed on port `39741`, *not* on port `22`. Meanwhile, the same `onion-ssh` service running on `jumpbox2.example.com` will be exposed on port `12946`. Nevertheless, both jump boxes will still have `auth_type: stealth` and the same `clients` list defined. Only the `port_number` and `target_port` variables will be overriden, because only they are defined in the service's dictionary in the `onion_services_overrides` list.

#### Enabling and disabling Onion service configurations

Onion service configurations are stored in `/etc/tor/torrc.d/onions-available` and enabled by symlinking them from `/etc/tor/torrc.d/onions-enabled`. The `onions-enabled` directory is `%include`'ed via the main Tor configuration file, `/etc/tor/torrc`. To manually enable an available configuration, symlink the file for the appropriate Onion service to the `/etc/tor/torrc.d/onions-enabled` directory and reload the Tor service (by sending the main Tor process a `HUP` signal, e.g., `sudo systemctl reload tor` or directly `sudo killall --signal HUP tor`). To manually disable an Onion, unlink the file from the `onions-enabled` directory and reload the Tor service again.

The symlinks are handled by the `enabled` key, described above, so you can do something like the following to disable but not remove an Onion service configuration:

```yaml
onion_services:
  - name: my-service
    enabled: absent
    virtports:
      - port_number: 80
```

With such a configuration, the `/etc/tor/torrc.d/onions-available/my-service` file will exist, but it will not be symlinked from `/etc/tor/torrc.d/onions-enabled/my-service`.

You can also ensure that any given Onion service configurations, along with its private (and client) keys, are wiped from the expected places on disk:

```yaml
onion_services:
  - name: my-service
    state: absent
```

The above will ensure that the `onions-enabled/my-service` file, the `onions-available/my-service` file, and the `/var/lib/tor/onion-services/my-service` directory hierarchy will be deleted. Note that since a completely missing configuration cannot be enabled, if you specify `state: absent`, the value of `enabled` is ignored.

### Onion service client configuration variables

There is zero additional configuration required on your part in order to connect to unauthenticated Onion services. However, an Onion service server may require that a Tor client authenticate itself before responding to its requests. Such Onion services are termed *authenticated Onion services* because they require client authentication before passing traffic to its real service.

Use the `onion_services_client_credentials` list to [configure authentication credentials](https://www.torproject.org/docs/tor-manual.html#HiddenServiceAuthorizeClient) for a given client at a given Onion service. Each item in this list is a dictionary with the following keys:

* `domain`: Onion domain name (including the literal `.onion` suffix) of the Onion service to which you will be authenticating. This key is required.
* `cookie`: Authentication cookie value with which you will authenticate. This key is required.
* `comment`: Human-readable comment describing the Onion service to which the authentication credentials belong. This key is optional.

The `domain` and `cookie` keys function like a username/password combination and should therefore be encrypted using [Ansible Vault](https://docs.ansible.com/ansible/latest/user_guide/vault.html) whenever they appear in a playbook.

Some examples may prove helpful. Note that these authentication cookie values are intentionally not legitimate and will fail if used with `tor --verify-config`.

1. Authenticate to the Onion service at `nzh3fv6jc6jskki3.onion` using the authentication cookie value `Fjabcdef01234567890+/K`:
    ```yaml
    onion_services_client_credentials:
      - domain: nzh3fv6jc6jskki3.onion
        cookie: Fjabcdef01234567890+/K
    ```
    The above will create a configuration line such as the following:
    ```
    HidServAuth nzh3fv6jc6jskki3.onion Fjabcdef01234567890+/K
    ```
1. Authenticate to two different Onion services, while providing a comment for the latter of them:
    ```yaml
    onion_services_client_credentials:
      - domain: uj3wazyk5u4hnvtk.onion
        cookie: Fjabcdef01234567890+/K
      - domain: nzh3fv6jc6jskki3.onion
        cookie: K/+7abc098def7654321Fj
        comment: Friendly message board.
    ```
    The above will create two separate configuration lines:
    ```
    HidServAuth uj3wazyk5u4hnvtk.onion Fjabcdef01234567890+/K
    HidServAuth nzh3fv6jc6jskki3.onion K/+7abc098def7654321Fj Friendly message board.
    ```

Again, in a production playbook or vars file, these values should be encrypted using Ansible Vault. See [Ansible's documentation for `encrypt_string`](https://docs.ansible.com/ansible/latest/user_guide/vault.html#encrypt-string-for-use-in-yaml) for instructions on encrypting single values in YAML files. See AnarchoTech NYC's "[Connecting to an authenticated Onion service](https://github.com/AnarchoTechNYC/meta/wiki/Connecting-to-an-authenticated-Onion-service)" guide for more general details on the `HidServAuth` configuration directive.

These `HidServAuth` lines will be written to the file at `/etc/tor/torrc.d/client-auth` which is `%include`'ed in the main `/etc/tor/torrc` configuation file.

## Additional role variables

In addition to [configuring Onion services](#configuring-onion-services) themselves, you can configure various aspects of the Tor service and this role's behavior. The primary method of configuring Tor is via the `torrc` dictionary. Its keys map nearly one-to-one to the Tor configuration options described in the [Tor Manual](https://www.torproject.org/docs/tor-manual.html). Where the Tor configuration allows for multiple options of the same name, the `torrc` dictionary key names have been pluralized and accept lists instead of single (scalar) values. For Tor configuration options that expect a boolean in the form of `0` for false and `1` for true, integers or booleans (`false`/`true`) may be used.  For example:

* `torrc.DataDirectory`: System Tor root data directory. Defaults to `/var/lib/tor`. Maps to the Tor [DataDirectory](https://www.torproject.org/docs/tor-manual.html#DataDirectory) configuration option.
* `torrc.ControlSocket`: Path to a UNIX domain socket that will accept Tor controller connections. Maps to the Tor [ControlSocket](https://www.torproject.org/docs/tor-manual.html#ControlSocket) configuration option.
* `torrc.HashedControlPasswords`: List whose items are the equivalent of `HashedControlPassword` directives. Maps to the Tor [HashedControlPassword](https://www.torproject.org/docs/tor-manual.html#HashedControlPassword) configuration option.
* `torrc.CookieAuthentication`: Whether or not to enable Tor controller cookie-based authentication. A value of `0` or `false` disables cookie authentication, while `1` or `true` enables it. Maps to the Tor [CookieAuthentication](https://www.torproject.org/docs/tor-manual.html#CookieAuthentication) configuration option.

Moreover, you can alter this role's behavior by setting any of the following default variables:

* `tor_onion_services_backup_dir`: Path on the Ansible controller where configured Onion service private and client keys are stored for backup purposes. This is left undefined (commented out) by default, causing backup tasks to be skipped.
* `tor_onion_services_backup_password`: The password with which to encrypt backups of Onion service secrets. This value should itself be encrypted! Create it with a command such as [`ansible-vault encrypt_string`](https://docs.ansible.com/ansible/latest/user_guide/vault.html#encrypt-string-for-use-in-yaml). If left undefined (commented out), backups will not be encrypted, which is almost certainly not what you want.
* `tor_onion_services_backup_vault_id`: An optional [Ansible Vault ID](https://docs.ansible.com/ansible/latest/user_guide/vault.html#vault-ids-and-multiple-vault-passwords) with which to label encrypted Onion service backup files. This makes it possible to use a separate password for Tor backups than other secrets in your playbooks. By default, this will be the empty string (`''`), which is equivalent to no Vault ID.
* `tor_onion_services_dir`: Parent directory of individual Onion service directories. Defaults to `{{ torrc.DataDirectory }}/onion-services`
* `tor_onion_services_vanguards`: Dictionary of options to pass to the Vanguards add-on. Its keys are:
    * `version`: Git branch, tag, or commit hash to pass to `git checkout` when installing Vanguards.
    * `args`: Dictionary of command line arguments to pass to the invocation of the `vanguards.py` script. This key is required, even if it remains empty. For example:
        ```yaml
        args:
          control_port: "{{ torrc.ControlPort.port }}"
          disable_bandguards: true
          enable_cbtverify: true
        ```
        Assuming `torrc.ControlPort.port` is `9151`, this will result in an invocation of the form `./src/vangaurds.py --control_port 9151 --enable_cbtverify --disable_bandguards`.
        Alternatively, invoke the `vanguards.py` executable without any command line arguments by passing an empty dict:
        ```yaml
        args:
        ```
    * `config`: Dictionary of configuration file options. This is arguably a better place to put any Tor controller hashed password since it does not expose the hashed password on the command line. For example:
        ```yaml
        args:
          config: "/etc/tor/vanguards.conf"
        config:
          control_pass: "{{ torrc.HashedControlPasswords[0] }}"
        ```
        See the [Vanguards configuration file template](templates/vanguards.conf.j2) for details about configuration file options.
* `tor_package_build_dir`: Directory in which to (re)build from source, if necessary. This directory is automatically created with `"700"` permission bits and removed upon successful re-installation. Defaults to `/tmp/tor-package-source`.

Read the comments in [defaults/main.yaml](defaults/main.yaml) for a complete accounting of this role's default variables.

## Maintaining Tor

Merely installing Tor is not sufficient for environments where [NetSec](https://github.com/AnarchoTechNYC/meta/wiki/NetSec) considerations are critical. The installed Tor software must be kept up-to-date to, for example, have security patches applied. This Ansible role therefore compares the installed version of the system Tor against the latest source release provided by the Tor Project and will rebuild Tor from source whenever a newer version becomes available. This happens *every* time an Ansible play that includes this role is run.

Building Tor from source can take a significant amount of time on extremely low-power hardware. (It takes ~1 hour on a Raspberry Pi model 1.) Since this can be a concern in its own right, these tasks are tagged `tor-build` and can be skipped by invoking `ansible` or `ansible-playbook` with the `--skip-tags tor-build` command-line option. See the [Role tags](#role-tags) section for more details.

## Managing backup passwords

If you choose to use this role's `*backup*` variables, you are responsible for setting strong passwords. There are two passwords involved in this role's Onion service backups:

1. Password used by the Ansible runtime that encrypts and decrypts the backup copies of Onion service key files themselves during play execution. We call this the *backup password*.
1. Password entered by a human operator that is used to decrypt the first password for use by Ansible. We call this the *controller password*.

Safely making the backup password will look something like this:

```sh
openssl rand -base64 48 | ansible-vault encrypt_string > /tmp/vault-pass.out
```

You will then be prompted to enter (and then confirm) the controller password. Be sure you store this second, controller password somewhere you can access it again safely, perhaps by using a password/secrets management application. (Please see "[Strengthening Passwords to Defend Against John](https://github.com/AnarchoTechNYC/meta/tree/master/train-the-trainers/mr-robots-netflix-n-hack/week-2/strengthening-passwords-to-defend-against-john/README.md)" for more details about general password safety and hygiene.) When executing your playbooks that use this feature, you will need to invoke Ansible with the `--vault-id` option in order to supply the controller password so that Ansible can decrypt the backup password.

To retrieve the backup password manually, you can [invoke an ad-hoc command](https://docs.ansible.com/ansible/latest/user_guide/intro_adhoc.html) such as the following:

```sh
ansible localhost -i inventories/example/hosts -m debug -a "msg={{ tor_onion_services_backup_password | trim }}" --vault-id @prompt
```

This will prompt you for the controller password and will show you the backup password.

## Role tags

The following tags are provided by this role:

* `tor-build` - Tasks that build Tor from source.
* `tor-backup` - Tasks that fetch and then protect Onion service secrets (i.e., `private_key` and `client_keys` files).
