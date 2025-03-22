SELECT user_id, COUNT(*) AS session_count
FROM sessions
GROUP BY user_id
ORDER BY session_count DESC;
