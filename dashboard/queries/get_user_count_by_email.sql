SELECT
    COUNT(*) AS user_count
FROM users
WHERE email = %s;