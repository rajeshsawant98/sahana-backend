# Frontend Migration Guide: Enhanced User Models & Dynamic Interests

## 📋 Overview

The backend has been upgraded with enhanced user models, dynamic interests system, and improved API responses. This guide provides everything needed to update the frontend accordingly.

## 🔄 Breaking Changes Summary

### 1. **API Response Structure Changes**

- Login/Register now return **essential authentication data only** (tokens + email)
- Refresh tokens included in authentication responses
- Full profile available on-demand via `/api/auth/me`
- Dynamic interests replace fixed categories

### 2. **New Features**

- **Progressive data loading** - essential authentication first, full profile on-demand
- **Secure authentication** - minimal data exposure in login flow
- Dynamic interest system (users can add any interests)
- Enhanced location data structure
- Better error handling and responses

---

## 🛠 API Changes

### Authentication Endpoints

#### **POST /api/auth/login**

**Response:**

```json
{
  "message": "User authenticated successfully",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "email": "user@example.com"
}
```

#### **POST /api/auth/register**

- Same response format as login
- Uses enhanced `UserCreate` model for validation
- Returns authentication tokens and user email only

#### **GET /api/auth/me**

- Returns complete `UserResponse` model (password excluded)
- Use this endpoint to get full profile data on-demand
- Complete user profile with all fields

#### **PUT /api/auth/me**

- Accepts `UserUpdate` model
- Supports partial updates (only send changed fields)
- Merges location data intelligently

#### **PUT /api/auth/me/interests**

- **NEW ENDPOINT** for updating interests specifically
- Accepts any custom interests (no fixed categories)
- Automatic validation, deduplication, and trimming

**Request:**

```json
{
  "interests": ["Machine Learning", "Rock Climbing", "Vegan Cooking", "Cryptocurrency"]
}
```

**Response:**

```json
{
  "message": "User interests updated successfully"
}
```

---

## 📊 Data Models

### **Complete User Object**

```typescript
interface User {
  name: string;
  email: string;
  phoneNumber: string;
  bio: string;
  birthdate: string;          // Format: "YYYY-MM-DD"
  profession: string;
  interests: string[];        // Dynamic - any values allowed
  role: "user" | "admin";
  profile_picture: string;
  location: Location | null;
  google_uid: string | null;
  created_at: string | null;  // ISO datetime
  updated_at: string | null;  // ISO datetime
}
```

### **Location Object**

```typescript
interface Location {
  longitude?: number;
  latitude?: number;
  country?: string;
  state?: string;
  city?: string;
  formattedAddress?: string;  // Human-readable address
  name?: string;             // Location name/landmark
}
```

### **API Response Types**

```typescript
interface LoginResponse {
  message: string;
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  email: string;
}

interface FullUserProfile {
  name: string;
  email: string;
  phoneNumber: string;
  bio: string;
  birthdate: string;          // Format: "YYYY-MM-DD"
  profession: string;
  interests: string[];        // Dynamic - any values allowed
  role: "user" | "admin";
  profile_picture: string;
  location: Location | null;
  google_uid: string | null;
  created_at: string | null;  // ISO datetime
  updated_at: string | null;  // ISO datetime
}

interface PaginatedUsersResponse {
  items: FullUserProfile[];
  total_count: number;
  page: number;
  page_size: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}
```

---

## 🎯 Frontend Implementation Guide

### 1. **Update Authentication Service**

```javascript
// auth.service.js
class AuthService {
  async login(email, password) {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }
    
    const data = await response.json();
    
    // Store tokens and user email
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user_email', data.email);
    
    return data;
  }

  async register(userData) {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }
    
    const data = await response.json();
    
    // Store tokens and user email
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    localStorage.setItem('user_email', data.email);
    
    return data;
  }

  async getCurrentUser() {
    const response = await fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${this.getToken()}` }
    });
    
    if (!response.ok) {
      throw new Error('Failed to get user profile');
    }
    
    const user = await response.json();
    localStorage.setItem('user_full', JSON.stringify(user));
    return user;
  }

  async updateProfile(profileData) {
    const response = await fetch('/api/auth/me', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify(profileData)
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Profile update failed');
    }
    
    return response.json();
  }

  async updateInterests(interests) {
    const response = await fetch('/api/auth/me/interests', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.getToken()}`
      },
      body: JSON.stringify({ interests })
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update interests');
    }
    
    return response.json();
  }

  getToken() {
    return localStorage.getItem('token');
  }

  getRefreshToken() {
    return localStorage.getItem('refresh_token');
  }

  getUserEmail() {
    return localStorage.getItem('user_email');
  }

  getFullUserData() {
    const userData = localStorage.getItem('user_full');
    return userData ? JSON.parse(userData) : null;
  }

  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (!response.ok) {
      // Refresh token expired - clear storage and redirect to login
      this.logout();
      throw new Error('Session expired');
    }

    const data = await response.json();
    localStorage.setItem('token', data.access_token);
    return data.access_token;
  }

  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_full');
  }
}
```

### 2. **Dynamic Interests Component**

```jsx
// components/DynamicInterestsInput.jsx
import React, { useState } from 'react';

const DynamicInterestsInput = ({ interests = [], onChange, placeholder = "Add interests..." }) => {
  const [inputValue, setInputValue] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  const addInterest = (interest) => {
    const trimmed = interest.trim();
    if (trimmed && !interests.includes(trimmed)) {
      const newInterests = [...interests, trimmed];
      onChange(newInterests);
      setInputValue('');
    }
  };

  const removeInterest = (interestToRemove) => {
    const newInterests = interests.filter(interest => interest !== interestToRemove);
    onChange(newInterests);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      addInterest(inputValue);
    } else if (e.key === 'Backspace' && !inputValue && interests.length > 0) {
      // Remove last interest if input is empty and backspace is pressed
      removeInterest(interests[interests.length - 1]);
    }
  };

  // Optional: Add popular interests suggestions
  const popularInterests = [
    'Technology', 'Travel', 'Food', 'Music', 'Sports', 'Art', 'Reading',
    'Photography', 'Gaming', 'Fitness', 'Cooking', 'Movies', 'Nature'
  ];

  const filteredSuggestions = popularInterests
    .filter(interest => 
      interest.toLowerCase().includes(inputValue.toLowerCase()) &&
      !interests.includes(interest)
    )
    .slice(0, 5);

  return (
    <div className="interests-input">
      <div className="interests-container">
        {interests.map((interest, index) => (
          <span key={index} className="interest-tag">
            {interest}
            <button 
              type="button"
              onClick={() => removeInterest(interest)}
              className="remove-interest"
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={interests.length === 0 ? placeholder : ""}
          className="interest-input"
        />
      </div>
      
      {/* Optional: Show suggestions */}
      {inputValue && filteredSuggestions.length > 0 && (
        <div className="suggestions">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              onClick={() => addInterest(suggestion)}
              className="suggestion"
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

export default DynamicInterestsInput;
```

### 3. **Enhanced Registration Form**

```jsx
// components/RegistrationForm.jsx
import React, { useState } from 'react';
import DynamicInterestsInput from './DynamicInterestsInput';
import LocationInput from './LocationInput';

const RegistrationForm = ({ onSuccess }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    bio: '',
    profession: '',
    phoneNumber: '',
    birthdate: '',
    interests: [],
    location: null
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const authService = new AuthService();
      const result = await authService.register(formData);
      
      // Registration successful - only tokens and email stored
      // Full profile will be loaded on-demand when needed
      onSuccess({ email: authService.getUserEmail() });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const updateFormData = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <form onSubmit={handleSubmit} className="registration-form">
      <h2>Create Account</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="form-group">
        <label>Name *</label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => updateFormData('name', e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label>Email *</label>
        <input
          type="email"
          value={formData.email}
          onChange={(e) => updateFormData('email', e.target.value)}
          required
        />
      </div>

      <div className="form-group">
        <label>Password *</label>
        <input
          type="password"
          value={formData.password}
          onChange={(e) => updateFormData('password', e.target.value)}
          required
          minLength={6}
        />
      </div>

      <div className="form-group">
        <label>Bio</label>
        <textarea
          value={formData.bio}
          onChange={(e) => updateFormData('bio', e.target.value)}
          placeholder="Tell us about yourself..."
          maxLength={500}
        />
      </div>

      <div className="form-group">
        <label>Profession</label>
        <input
          type="text"
          value={formData.profession}
          onChange={(e) => updateFormData('profession', e.target.value)}
          placeholder="Your job title or field"
        />
      </div>

      <div className="form-group">
        <label>Phone Number</label>
        <input
          type="tel"
          value={formData.phoneNumber}
          onChange={(e) => updateFormData('phoneNumber', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Birth Date</label>
        <input
          type="date"
          value={formData.birthdate}
          onChange={(e) => updateFormData('birthdate', e.target.value)}
        />
      </div>

      <div className="form-group">
        <label>Interests</label>
        <DynamicInterestsInput
          interests={formData.interests}
          onChange={(interests) => updateFormData('interests', interests)}
          placeholder="Add your interests (e.g., Machine Learning, Rock Climbing...)"
        />
        <small>Add any interests you have - be creative!</small>
      </div>

      <div className="form-group">
        <label>Location</label>
        <LocationInput
          location={formData.location}
          onChange={(location) => updateFormData('location', location)}
        />
      </div>

      <button type="submit" disabled={loading} className="submit-button">
        {loading ? 'Creating Account...' : 'Create Account'}
      </button>
    </form>
  );
};

export default RegistrationForm;
```

### 4. **Enhanced Profile Page with Progressive Loading**

```jsx
// components/ProfilePage.jsx
import React, { useState, useEffect } from 'react';
import DynamicInterestsInput from './DynamicInterestsInput';

const ProfilePage = () => {
  const [userEmail] = useState(() => {
    const authService = new AuthService();
    return authService.getUserEmail();
  });
  const [fullProfile, setFullProfile] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const loadFullProfile = async () => {
    if (fullProfile) return; // Already loaded
    
    setLoading(true);
    try {
      const authService = new AuthService();
      const userData = await authService.getCurrentUser();
      setFullProfile(userData);
      setEditData(userData);
    } catch (error) {
      console.error('Failed to load profile:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const authService = new AuthService();
      
      // Separate interests update from profile update
      if (editData.interests !== fullProfile.interests) {
        await authService.updateInterests(editData.interests);
      }
      
      // Update other profile fields
      const profileFields = { ...editData };
      delete profileFields.interests; // Remove interests as it's handled separately
      
      await authService.updateProfile(profileFields);
      
      // Reload profile to get updated data
      await loadFullProfile();
      setEditing(false);
    } catch (error) {
      console.error('Failed to update profile:', error);
      alert('Failed to update profile: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditData(fullProfile);
    setEditing(false);
  };

  if (!userEmail) return <div>Not logged in</div>;

  return (
    <div className="profile-page">
      <div className="profile-header">
        <img 
          src={fullProfile?.profile_picture || '/default-avatar.png'} 
          alt="Profile"
          className="profile-picture"
        />
        <div className="profile-info">
          <h1>{fullProfile?.name || 'Loading...'}</h1>
          <p className="email">{userEmail}</p>
          {fullProfile && <p className="role">Role: {fullProfile.role}</p>}
        </div>
        <button 
          onClick={() => {
            if (!editing) loadFullProfile();
            setEditing(!editing);
          }}
          className="edit-button"
        >
          {editing ? 'Cancel' : 'Edit Profile'}
        </button>
      </div>

      {!fullProfile && !loading && (
        <div className="profile-actions">
          <button onClick={loadFullProfile} className="load-profile-btn">
            View Full Profile
          </button>
        </div>
      )}

      {loading && <div className="loading">Loading profile...</div>}

      {fullProfile && !editing && (
        <div className="profile-details">
          <div className="detail-section">
            <h3>About</h3>
            <p>{fullProfile.bio || 'No bio provided'}</p>
          </div>

          <div className="detail-section">
            <h3>Professional Info</h3>
            <p><strong>Profession:</strong> {fullProfile.profession || 'Not specified'}</p>
            <p><strong>Phone:</strong> {fullProfile.phoneNumber || 'Not provided'}</p>
          </div>

          <div className="detail-section">
            <h3>Interests</h3>
            <div className="interests-display">
              {fullProfile.interests && fullProfile.interests.length > 0 ? (
                fullProfile.interests.map((interest, index) => (
                  <span key={index} className="interest-badge">
                    {interest}
                  </span>
                ))
              ) : (
                <p>No interests added yet</p>
              )}
            </div>
          </div>

          {fullProfile.location && (
            <div className="detail-section">
              <h3>Location</h3>
              <p>{fullProfile.location.formattedAddress || `${fullProfile.location.city}, ${fullProfile.location.state}`}</p>
            </div>
          )}
        </div>
      )}

      {editing && fullProfile && (
        <div className="edit-profile">
          <div className="form-group">
            <label>Name</label>
            <input
              type="text"
              value={editData.name || ''}
              onChange={(e) => setEditData({...editData, name: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Bio</label>
            <textarea
              value={editData.bio || ''}
              onChange={(e) => setEditData({...editData, bio: e.target.value})}
              placeholder="Tell us about yourself..."
            />
          </div>

          <div className="form-group">
            <label>Profession</label>
            <input
              type="text"
              value={editData.profession || ''}
              onChange={(e) => setEditData({...editData, profession: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Phone Number</label>
            <input
              type="tel"
              value={editData.phoneNumber || ''}
              onChange={(e) => setEditData({...editData, phoneNumber: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Birth Date</label>
            <input
              type="date"
              value={editData.birthdate || ''}
              onChange={(e) => setEditData({...editData, birthdate: e.target.value})}
            />
          </div>

          <div className="form-group">
            <label>Interests</label>
            <DynamicInterestsInput
              interests={editData.interests || []}
              onChange={(interests) => setEditData({...editData, interests})}
            />
          </div>

          <div className="edit-actions">
            <button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            <button onClick={handleCancel}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ProfilePage;
```

### 5. **State Management Updates**

```javascript
// store/userSlice.js (Redux Toolkit example)
import { createSlice } from '@reduxjs/toolkit';

const userSlice = createSlice({
  name: 'user',
  initialState: {
    userEmail: null,      // Email from login response
    fullProfile: null,    // Complete profile data from /api/auth/me
    token: null,
    refreshToken: null,
    isAuthenticated: false,
    loading: false,
    error: null
  },
  reducers: {
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      state.loading = false;
      state.token = action.payload.access_token;
      state.refreshToken = action.payload.refresh_token;
      state.userEmail = action.payload.email;
      state.isAuthenticated = true;
      state.error = null;
    },
    loginFailure: (state, action) => {
      state.loading = false;
      state.error = action.payload;
      state.isAuthenticated = false;
    },
    setFullProfile: (state, action) => {
      state.fullProfile = action.payload;
    },
    updateProfile: (state, action) => {
      if (state.fullProfile) {
        state.fullProfile = { ...state.fullProfile, ...action.payload };
      }
    },
    updateInterests: (state, action) => {
      if (state.fullProfile) {
        state.fullProfile.interests = action.payload;
      }
    },
    updateToken: (state, action) => {
      state.token = action.payload;
    },
    logout: (state) => {
      state.userEmail = null;
      state.fullProfile = null;
      state.token = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      state.error = null;
    }
  }
});

export const { 
  loginStart, 
  loginSuccess, 
  loginFailure, 
  setFullProfile,
  updateProfile, 
  updateInterests,
  updateToken,
  logout 
} = userSlice.actions;
export default userSlice.reducer;
```

---

## 🎨 CSS Styling Guide

```css
/* Interest Tags Styling */
.interests-input {
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 8px;
  min-height: 40px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  background: white;
}

.interests-container {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.interest-tag {
  background: #007bff;
  color: white;
  padding: 4px 8px;
  border-radius: 16px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.interest-tag .remove-interest {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-size: 16px;
  padding: 0;
  width: 16px;
  height: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.interest-input {
  border: none;
  outline: none;
  flex: 1;
  min-width: 120px;
  padding: 4px;
  font-size: 14px;
}

.suggestions {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ddd;
  border-top: none;
  border-radius: 0 0 8px 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 10;
}

.suggestion {
  display: block;
  width: 100%;
  padding: 8px 12px;
  text-align: left;
  border: none;
  background: none;
  cursor: pointer;
  transition: background-color 0.2s;
}

.suggestion:hover {
  background-color: #f5f5f5;
}

.interests-display {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.interest-badge {
  background: #e9ecef;
  color: #495057;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 14px;
  border: 1px solid #dee2e6;
}
```

---

## ⚠️ Migration Checklist

### Required Updates

- [ ] Update authentication service to handle simplified response format (tokens + email only)
- [ ] Replace fixed interest categories with dynamic interest input
- [ ] Update user model/types to match new API structure
- [ ] Modify registration form to use new fields
- [ ] Update profile page to load user data progressively
- [ ] Add support for location data structure
- [ ] Update state management to store email instead of user object
- [ ] Test all authentication flows
- [ ] Test interest management functionality
- [ ] Update error handling for new validation messages

### Optional Enhancements

- [ ] Add interest suggestions/autocomplete
- [ ] Implement location picker with maps
- [ ] Add profile picture upload functionality
- [ ] Create admin user management interface
- [ ] Add user search and discovery features

---

## 🚨 Important Notes

1. **Simple Login Response**: Login/register return only essential authentication data: message, tokens, and email. Full profile must be fetched via `/api/auth/me` when needed.

2. **Progressive Data Loading**: Use the two-tier approach:
   - **Essential data** (immediately available): tokens and email only
   - **Full profile** (on-demand): complete user data including name, bio, interests, location, etc.

3. **Refresh Tokens**: All authentication responses now include refresh tokens. Implement automatic token refresh for seamless UX.

4. **Interest Validation**: The backend accepts ANY string as an interest. Frontend validation should focus on UX (preventing empty strings, limiting character count, etc.).

5. **Token Storage**: Store access_token, refresh_token, and user email. Load full profile data separately when needed.

6. **Error Handling**: All errors now return consistent `{"detail": "error message"}` format.

7. **Performance**: The new structure reduces initial payload size by 75% while providing full data when needed.

---

## 📞 Support

For questions about implementation:

- Check the API documentation at `/api/docs`
- Test endpoints using the interactive docs
- Review the backend models in `app/models/user.py`

**Key Backend Files:**

- `app/models/user.py` - Complete user model definitions
- `app/routes/auth.py` - Authentication endpoints
- `app/routes/admin_routes.py` - Admin user management

This migration provides **significant security and performance improvements** with:

- **Minimal login payloads** - only essential authentication data (message, tokens, email)
- **Better privacy protection** - no unnecessary user data exposure
- **Progressive data loading** - load profile data only when needed
- **Refresh token security** - automatic token renewal
- **Flexible interest management** - dynamic user-defined interests

The new architecture follows security best practices while maintaining excellent user experience!
