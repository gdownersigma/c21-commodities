INSERT INTO users (
    user_name,
    email, 
    password)
VALUES (%s, %s, %s)
RETURNING user_id;