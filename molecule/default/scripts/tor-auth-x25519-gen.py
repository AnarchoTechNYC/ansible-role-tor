#!/usr/bin/env python3
"""Tor v3 Onion authentication credential generator script.

This module outputs Tor Onion v3 Onion credentials and generates the
associated X25519 cryptographic keypairs for use in those credential
files. The PyNaCl library is required. To install it, for example:

```sh
pip install pynacl
```
"""

import base64
import sys, argparse, re

try:
    import nacl.public
except ImportError:
    print('PyNaCl is required: "pip install pynacl" or similar')
    exit(1)

def key_str(key):
    # bytes to base 32
    key_bytes = bytes(key)
    key_b32 = base64.b32encode(key_bytes)
    # strip trailing ====
    assert key_b32[-4:] == b'===='
    key_b32 = key_b32[:-4]
    # change from b'ASDF' to ASDF
    s = key_b32.decode('utf-8')
    return s

def validate_onion(v):
    """Ensure the given Onion domain is valid.

    Args:
        v (str): The given value.

    Returns:
        str: The validated value.

    Raises:
        ArgumentTypeError: If `v` does not validate.

    >>> validate_onion('value with incorrect ending')
    Traceback (most recent call last):
        ...
    argparse.ArgumentTypeError: Onion domain must end in ".onion"

    >>> validate_onion('tooShortValue.onion')
    Traceback (most recent call last):
        ...
    argparse.ArgumentTypeError: Onion domains must be 56 lowercased alphanumeric characters.

    >>> validate_onion('Onions Must Be 56 Entirely Lowercased Alphanumeric Chars.onion')
    Traceback (most recent call last):
        ...
    argparse.ArgumentTypeError: Onion domains must be 56 lowercased alphanumeric characters.

    >>> validate_onion('rh5d6reakhpvuxe2t3next6um6iiq4jf43m7gmdrphfhopfpnoglzcyd.onion')
    'rh5d6reakhpvuxe2t3next6um6iiq4jf43m7gmdrphfhopfpnoglzcyd'
    """

    onion = v.split('.')[0]

    if not v.endswith('.onion'):
        raise argparse.ArgumentTypeError('Onion domain must end in ".onion"')
    if not re.match('[a-z0-9]{56}', onion):
        raise argparse.ArgumentTypeError('Onion domains must be 56 lowercased alphanumeric characters.')

    return onion

def main():
    parser = argparse.ArgumentParser(description="Generate a new X25519 keypair and output Tor Onion service credential file contents.")
    parser.add_argument(
        "-d", "--onion-domain",
        help="Onion domain for which to create a keypair. Include the `.onion` part.",
        type=validate_onion
    )
    args = parser.parse_args()

    priv_key = nacl.public.PrivateKey.generate()
    pub_key  = priv_key.public_key
    if args.onion_domain:
        print('# Public key (`.auth` file) content follows. Give this to the Onion service operator.')
        print(f'descriptor:x25519:{key_str(pub_key)}')
        print('# Private key (`.auth_private` file) content follows. Use this to configure your own Tor client.')
        print(f'{args.onion_domain}:descriptor:x25519:{key_str(priv_key)}')
    else:
        print(f'secret: {key_str(priv_key)}')
        print(f'public: {key_str(pub_key)}')

if __name__ == '__main__':
    exit(main())
