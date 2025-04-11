import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", type=str, help="registration, imap, verification, update, import, export")
    parser.add_argument("--accounts", type=str, default='accounts.txt', help="path to log:mail_pass file, default='accounts.txt'")
    parser.add_argument("--proxy", type=str, default='proxy.txt', help="path to proxy.txt, default = proxy.txt'")
    parser.add_argument("--rotate", type=int, default= 82000, help="time rotate ip proxy in seconds, default = 82000")
    parser.add_argument("--ref", type=str, default='referral.txt', help="path to referral.txt, default = referral.txt'")
    parser.add_argument("--captcha_service", type=str, default='capmonster', help="captcha service. Supports capmonster, anticaptcha, 2captcha, capsolver, captchaai")
    parser.add_argument("--captcha_key", type=str, default='', help="captcha api key, default = '' ")
    parser.add_argument("--threads", type=int, default= 1, help="asyncio semaphore, default = 1")
    parser.add_argument("--debug", type=bool, default=False, help="Debug mode, default = False")
    parser.add_argument("--imap", type=str, default= '', help="Only one imap domain")
    parser.add_argument("--imap_proxy", type=str, default= '', help="If imap server requires a specific location, default=None")
    parser.add_argument("--forward_mode", type=bool, default=False, help=", default=False")
    parser.add_argument("--file_name", type=str, default= 'example', help="File name. Expample: my_file")
    parser.add_argument("--format", type=str, default= 'email:password', help="Set the parameters and the separator as in your file. Example: email:password:password_email:imap_domain:wallet:private_key:seed")
    parser.add_argument("--separator", type=str, default= ':', help="Separator for import or export data accounts")
    parser.add_argument("--export_type", type=str, default= 'excel', help="Export file type. excel or txt")

    return parser.parse_args()

def update_args(old: argparse.Namespace, new: dict):
    for k,v in new.items():
        if hasattr(old, k):
            setattr(old, k, v)
    return old

