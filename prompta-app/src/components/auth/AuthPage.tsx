
import { useState } from 'react';
import { LoginForm } from './LoginForm';
import { SignUpForm } from './SignUpForm';

export const AuthPage = () => {
  const [isSignUp, setIsSignUp] = useState(false);

  const toggleMode = () => {
    setIsSignUp(!isSignUp);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold">Prompta</h1>
          <p className="text-muted-foreground mt-2">
            AI Prompt Management Platform
          </p>
        </div>
        
        {isSignUp ? (
          <SignUpForm onToggleMode={toggleMode} />
        ) : (
          <LoginForm onToggleMode={toggleMode} />
        )}
      </div>
    </div>
  );
};
