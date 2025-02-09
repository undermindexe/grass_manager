from bip_utils import Bip39SeedGenerator, Bip44Coins, Bip44, base58, Bip44Changes
from nacl.signing import SigningKey
from mnemonic import Mnemonic
import time
import base64

class Wallet():
    def __init__(self):
        self.wallet = None
        self.private_key = None
        self.seed = None
        self.sign = None
        self.public_key = None

    def gen_wallet(self, seed = None):
        if seed == None:
            self.seed = Mnemonic("english").generate(strength=128)
        seed_bytes = Bip39SeedGenerator(self.seed).Generate('')
        bip44_mst_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.SOLANA)

        bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
        bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT) 
        priv_key_bytes = bip44_chg_ctx.PrivateKey().Raw().ToBytes()
        public_key_bytes = bip44_chg_ctx.PublicKey().RawCompressed().ToBytes()[1:]
        key_pair = priv_key_bytes+public_key_bytes
        self.wallet = bip44_chg_ctx.PublicKey().ToAddress()
        self.public_key = base64.b64encode(public_key_bytes).decode("utf-8")
        self.private_key = base58.Base58Encoder.Encode(key_pair)

        timestamp=int(time.time())
        sign = self.generate_sign(priv_key_bytes, timestamp)
        return sign, timestamp

    def generate_sign(self, priv_key_bytes, timestamp):
        message = f"""By signing this message you are binding this wallet to all activities associated to your Grass account and agree to our Terms and Conditions (https://www.getgrass.io/terms-and-conditions) and Privacy Policy (https://www.getgrass.io/privacy-policy).

Nonce: {timestamp}"""
        sign_key = SigningKey(priv_key_bytes)
        
        sign = sign_key.sign(message.encode('utf-8')).signature

        return base64.b64encode(sign).decode("utf-8")