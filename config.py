class Config:
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://root:root@localhost/ehr_system"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = "f8d88ec30c2e009dce1f76c91b0be88d458eb73dc152523f6258b8ba68b108ee"
    SECURITY_PASSWORD_SALT = "619cce89f6d4a67b485eb2b787016d2c"

    # SMTP config (example: Gmail – for dev/testing use an app password)
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "u2302900270@gmail.com"
    MAIL_PASSWORD = "swkc vdsl vyjh fdug"
    MAIL_DEFAULT_SENDER = ("EHR System", "u2302900270@gmail.com")
