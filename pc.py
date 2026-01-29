from werkzeug.security import generate_password_hash

new_password = "123456"
hashed_password = generate_password_hash(new_password)
print(hashed_password)

# username-- shreehari@gmail.com