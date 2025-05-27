import streamlit_authenticator as stauth

hashed_passwords = stauth.Hasher(['ASPLANVIAK123', 'TRONDHEIM123']).generate()
print(hashed_passwords)
