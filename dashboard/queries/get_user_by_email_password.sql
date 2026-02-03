SELECT
    user_name,
    email
FROM users
WHERE email = %s
    AND password = %s;