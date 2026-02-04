SELECT
    user_id,
    user_name,
    email
FROM users
WHERE email = %s
    AND password = %s;