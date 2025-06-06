-- Enable the auth schema
CREATE SCHEMA IF NOT EXISTS auth;

-- Create auth.users table if it doesn't exist
CREATE TABLE IF NOT EXISTS auth.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    encrypted_password TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_sign_in_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Create auth.sessions table
CREATE TABLE IF NOT EXISTS auth.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create auth.refresh_tokens table
CREATE TABLE IF NOT EXISTS auth.refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create auth.password_resets table
CREATE TABLE IF NOT EXISTS auth.password_resets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create auth.email_verifications table
CREATE TABLE IF NOT EXISTS auth.email_verifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON auth.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON auth.refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_resets_user_id ON auth.password_resets(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verifications_user_id ON auth.email_verifications(user_id);

-- Create functions for authentication

-- Function to create a new user
CREATE OR REPLACE FUNCTION auth.create_user(
    email TEXT,
    password TEXT
) RETURNS UUID AS $$
DECLARE
    user_id UUID;
BEGIN
    INSERT INTO auth.users (email, encrypted_password)
    VALUES (email, crypt(password, gen_salt('bf')))
    RETURNING id INTO user_id;
    
    RETURN user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to verify user credentials
CREATE OR REPLACE FUNCTION auth.verify_user(
    email TEXT,
    password TEXT
) RETURNS UUID AS $$
DECLARE
    user_id UUID;
BEGIN
    SELECT id INTO user_id
    FROM auth.users
    WHERE email = verify_user.email
    AND encrypted_password = crypt(verify_user.password, encrypted_password);
    
    RETURN user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create a session
CREATE OR REPLACE FUNCTION auth.create_session(
    user_id UUID
) RETURNS TEXT AS $$
DECLARE
    session_token TEXT;
BEGIN
    session_token := encode(gen_random_bytes(32), 'hex');
    
    INSERT INTO auth.sessions (user_id, token, expires_at)
    VALUES (user_id, session_token, NOW() + INTERVAL '24 hours');
    
    RETURN session_token;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to validate a session
CREATE OR REPLACE FUNCTION auth.validate_session(
    session_token TEXT
) RETURNS UUID AS $$
DECLARE
    user_id UUID;
BEGIN
    SELECT s.user_id INTO user_id
    FROM auth.sessions s
    WHERE s.token = session_token
    AND s.expires_at > NOW();
    
    RETURN user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create a refresh token
CREATE OR REPLACE FUNCTION auth.create_refresh_token(
    user_id UUID
) RETURNS TEXT AS $$
DECLARE
    refresh_token TEXT;
BEGIN
    refresh_token := encode(gen_random_bytes(32), 'hex');
    
    INSERT INTO auth.refresh_tokens (user_id, token, expires_at)
    VALUES (user_id, refresh_token, NOW() + INTERVAL '30 days');
    
    RETURN refresh_token;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to create a password reset token
CREATE OR REPLACE FUNCTION auth.create_password_reset(
    email TEXT
) RETURNS TEXT AS $$
DECLARE
    reset_token TEXT;
    user_id UUID;
BEGIN
    SELECT id INTO user_id
    FROM auth.users
    WHERE email = create_password_reset.email;
    
    IF user_id IS NULL THEN
        RETURN NULL;
    END IF;
    
    reset_token := encode(gen_random_bytes(32), 'hex');
    
    INSERT INTO auth.password_resets (user_id, token, expires_at)
    VALUES (user_id, reset_token, NOW() + INTERVAL '1 hour');
    
    RETURN reset_token;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to reset password
CREATE OR REPLACE FUNCTION auth.reset_password(
    reset_token TEXT,
    new_password TEXT
) RETURNS BOOLEAN AS $$
DECLARE
    user_id UUID;
BEGIN
    SELECT pr.user_id INTO user_id
    FROM auth.password_resets pr
    WHERE pr.token = reset_token
    AND pr.expires_at > NOW();
    
    IF user_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    UPDATE auth.users
    SET encrypted_password = crypt(new_password, gen_salt('bf'))
    WHERE id = user_id;
    
    DELETE FROM auth.password_resets
    WHERE token = reset_token;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create RLS policies for auth tables
ALTER TABLE auth.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.password_resets ENABLE ROW LEVEL SECURITY;
ALTER TABLE auth.email_verifications ENABLE ROW LEVEL SECURITY;

-- Create policies for auth tables
CREATE POLICY "Users can view their own data"
    ON auth.users
    FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own data"
    ON auth.users
    FOR UPDATE
    USING (auth.uid() = id);

-- Create triggers for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column(); 