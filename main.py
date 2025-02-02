from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
import wave
import numpy as np

def generate_rsa_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_key = private_key.public_key()
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private_pem, public_pem

def encrypt_message_rsa(public_key_pem, message):
    public_key = serialization.load_pem_public_key(public_key_pem)
    encrypted_message = public_key.encrypt(
        message.encode(),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return encrypted_message

def decrypt_message_rsa(private_key_pem, encrypted_message):
    private_key = serialization.load_pem_private_key(private_key_pem, password=None)
    decrypted_message = private_key.decrypt(
        encrypted_message,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    return decrypted_message.decode()

def encode_audio_rsa(input_audio, output_audio, encrypted_message, end_marker='\x00'):
    audio = wave.open(input_audio, 'rb')
    frames = audio.readframes(audio.getnframes())
    audio_frames = np.frombuffer(frames, dtype=np.int16)
    message_binary = ''.join(format(byte, '08b') for byte in encrypted_message)
    message_length = len(message_binary)
    for i in range(message_length):
        audio_frames[i] = (audio_frames[i] & ~1) | int(message_binary[i])
    with wave.open(output_audio, 'wb') as output_audio_file:
        output_audio_file.setparams(audio.getparams())
        output_audio_file.writeframes(audio_frames.tobytes())
    audio.close()

def decode_audio_rsa(input_audio, private_key_pem, end_marker='\x00'):
    audio = wave.open(input_audio, 'rb')
    frames = audio.readframes(audio.getnframes())
    audio_frames = np.frombuffer(frames, dtype=np.int16)
    message_binary = ''
    for frame in audio_frames:
        message_binary += str(frame & 1)
    message = ''
    for i in range(0, len(message_binary), 8):
        byte = message_binary[i:i+8]
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        if char == end_marker:
            break
        message += char
    decrypted_message = decrypt_message_rsa(private_key_pem, message.encode())
    audio.close()
    return decrypted_message

private_key_pem, public_key_pem = generate_rsa_keys()
message = 'this is a secret message!'
encrypted_message = encrypt_message_rsa(public_key_pem, message)
encode_audio_rsa('path_to_input_audio.wav', 'path_to_output_audio.wav', encrypted_message)
decoded_message = decode_audio_rsa('path_to_output_audio.wav', private_key_pem)
print(f"Decoded message: {decoded_message}")
