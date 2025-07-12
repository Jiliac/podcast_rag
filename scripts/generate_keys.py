from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

def generate_and_print_keys():
    """Generates an RSA key pair and prints them for the .env file."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Serialize private key in PKCS#8 format, which is widely compatible
    private_pem = private_key.private_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PrivateFormat.PKCS8,
       encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    # Serialize public key
    public_pem = private_key.public_key().public_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    print("Copy the following lines into your .env file at the project root:")
    print("=" * 60)
    print(f'MCP_PRIVATE_KEY="""{private_pem}"""')
    print(f'MCP_PUBLIC_KEY="""{public_pem}"""')
    print("=" * 60)

if __name__ == "__main__":
    generate_and_print_keys()
