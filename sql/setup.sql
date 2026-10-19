IF OBJECT_ID(N'dbo.app_users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.app_users (
        id INT IDENTITY(1,1) PRIMARY KEY,
        username NVARCHAR(100) NOT NULL UNIQUE,
        display_name NVARCHAR(150) NOT NULL,
        password_salt VARCHAR(32) NOT NULL,
        password_hash VARCHAR(64) NOT NULL
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.app_users WHERE username = N'demo')
BEGIN
    INSERT INTO dbo.app_users
        (username, display_name, password_salt, password_hash)
    VALUES
        (N'demo', N'Demo User',
         '00112233445566778899aabbccddeeff',
         '67471425caaffaa51d11079ddc256f4f2933d86834c664bdaf16f5e7c7301246');
END;