# Friends System Frontend Implementation Guide

This document provides a complete guide for implementing the Friends system frontend in Sahana using React 19, TypeScript, Vite, Redux Toolkit, and Material-UI.

## Overview

The Friends system allows users to search for other users, send friend requests, manage incoming/outgoing requests, and maintain a friends list. This guide covers all frontend components, state management, and API integration.

## Architecture

```
Frontend Stack:
- React 19 + TypeScript
- Vite (Build tool)
- Redux Toolkit (State management)
- Material-UI (UI components)
- React Query/SWR (Data fetching & caching)
```

## Project Structure

```
src/
├── components/friends/
│   ├── FriendRequestCard.tsx
│   ├── FriendCard.tsx
│   ├── FriendSearch.tsx
│   ├── FriendsList.tsx
│   ├── PendingRequests.tsx
│   └── index.ts
├── pages/
│   ├── Friends.tsx
│   └── FriendRequests.tsx
├── redux/
│   ├── slices/
│   │   ├── friendsSlice.ts
│   │   └── friendRequestsSlice.ts
│   └── store.ts
├── services/
│   ├── api/
│   │   ├── friendsApi.ts
│   │   └── index.ts
│   └── types/
│       ├── friends.ts
│       └── api.ts
├── hooks/
│   ├── useFriends.ts
│   ├── useFriendRequests.ts
│   └── useDebounce.ts
└── utils/
    ├── friendsHelpers.ts
    └── constants.ts
```

## Type Definitions

Create comprehensive TypeScript types for the Friends system:

**`src/services/types/friends.ts`**

```typescript
export interface User {
  id: string;
  name: string;
  email: string;
  bio?: string;
  profile_picture?: string;
  location?: {
    address: string;
    latitude: number;
    longitude: number;
  };
  interests?: string[];
  events_created?: number;
  events_attended?: number;
  created_at?: string;
}

export interface FriendProfile extends User {
  events_created: number;
  events_attended: number;
}

export interface UserSearchResult extends User {
  friendship_status: 'none' | 'friends' | 'pending_sent' | 'pending_received';
}

export interface FriendRequest {
  id: string;
  sender: FriendProfile;
  receiver: FriendProfile;
  status: 'pending' | 'accepted' | 'rejected';
  created_at: string;
  updated_at?: string;
}

export interface FriendRequestsResponse {
  received: FriendRequest[];
  sent: FriendRequest[];
}

export interface SendFriendRequestPayload {
  receiver_id: string;
}

export interface FriendshipStatusResponse {
  friendship_status: 'none' | 'friends' | 'pending_sent' | 'pending_received';
}

// UI State Types
export interface FriendsUIState {
  searchTerm: string;
  searchResults: UserSearchResult[];
  isSearching: boolean;
  selectedTab: 'friends' | 'requests' | 'search';
}

export interface FriendRequestsUIState {
  activeTab: 'received' | 'sent';
  isLoading: boolean;
  errors: Record<string, string>;
}
```

## API Service Layer

**`src/services/api/friendsApi.ts`**

```typescript
import { 
  FriendProfile, 
  UserSearchResult, 
  FriendRequest, 
  FriendRequestsResponse,
  SendFriendRequestPayload,
  FriendshipStatusResponse 
} from '../types/friends';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

class FriendsApiService {
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const token = localStorage.getItem('accessToken');
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Network error' }));
      throw new Error(error.detail || 'API request failed');
    }

    return response.json();
  }

  // Send friend request
  async sendFriendRequest(payload: SendFriendRequestPayload): Promise<{ message: string; request_id: string }> {
    return this.request('/friends/request', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Get friend requests (both sent and received)
  async getFriendRequests(): Promise<FriendRequestsResponse> {
    return this.request('/friends/requests');
  }

  // Accept friend request
  async acceptFriendRequest(requestId: string): Promise<{ message: string }> {
    return this.request(`/friends/accept/${requestId}`, {
      method: 'POST',
    });
  }

  // Reject friend request
  async rejectFriendRequest(requestId: string): Promise<{ message: string }> {
    return this.request(`/friends/reject/${requestId}`, {
      method: 'POST',
    });
  }

  // Cancel sent friend request
  async cancelFriendRequest(requestId: string): Promise<{ message: string }> {
    return this.request(`/friends/request/${requestId}`, {
      method: 'DELETE',
    });
  }

  // Get friends list
  async getFriendsList(): Promise<FriendProfile[]> {
    return this.request('/friends/list');
  }

  // Search users
  async searchUsers(query: string, limit: number = 20): Promise<UserSearchResult[]> {
    const params = new URLSearchParams({ q: query, limit: limit.toString() });
    return this.request(`/friends/search?${params}`);
  }

  // Get friendship status
  async getFriendshipStatus(userId: string): Promise<FriendshipStatusResponse> {
    return this.request(`/friends/status/${userId}`);
  }
}

export const friendsApi = new FriendsApiService();
```

## Redux State Management

**`src/redux/slices/friendsSlice.ts`**

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { friendsApi } from '../../services/api/friendsApi';
import { FriendProfile, UserSearchResult, FriendsUIState } from '../../services/types/friends';

interface FriendsState {
  friends: FriendProfile[];
  searchResults: UserSearchResult[];
  ui: FriendsUIState;
  loading: {
    friends: boolean;
    search: boolean;
    sendRequest: boolean;
  };
  errors: {
    friends: string | null;
    search: string | null;
    sendRequest: string | null;
  };
}

const initialState: FriendsState = {
  friends: [],
  searchResults: [],
  ui: {
    searchTerm: '',
    searchResults: [],
    isSearching: false,
    selectedTab: 'friends',
  },
  loading: {
    friends: false,
    search: false,
    sendRequest: false,
  },
  errors: {
    friends: null,
    search: null,
    sendRequest: null,
  },
};

// Async Thunks
export const fetchFriends = createAsyncThunk(
  'friends/fetchFriends',
  async (_, { rejectWithValue }) => {
    try {
      const friends = await friendsApi.getFriendsList();
      return friends;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch friends');
    }
  }
);

export const searchUsers = createAsyncThunk(
  'friends/searchUsers',
  async ({ query, limit = 20 }: { query: string; limit?: number }, { rejectWithValue }) => {
    try {
      if (!query.trim()) return [];
      const results = await friendsApi.searchUsers(query, limit);
      return results;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to search users');
    }
  }
);

export const sendFriendRequest = createAsyncThunk(
  'friends/sendFriendRequest',
  async (receiverId: string, { rejectWithValue, dispatch }) => {
    try {
      const result = await friendsApi.sendFriendRequest({ receiver_id: receiverId });
      
      // Update search results to reflect the new pending status
      dispatch(updateSearchResultStatus({ userId: receiverId, status: 'pending_sent' }));
      
      return { receiverId, ...result };
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to send friend request');
    }
  }
);

const friendsSlice = createSlice({
  name: 'friends',
  initialState,
  reducers: {
    setSearchTerm: (state, action: PayloadAction<string>) => {
      state.ui.searchTerm = action.payload;
    },
    clearSearchResults: (state) => {
      state.searchResults = [];
      state.ui.searchTerm = '';
    },
    setSelectedTab: (state, action: PayloadAction<'friends' | 'requests' | 'search'>) => {
      state.ui.selectedTab = action.payload;
    },
    updateSearchResultStatus: (state, action: PayloadAction<{ userId: string; status: UserSearchResult['friendship_status'] }>) => {
      const { userId, status } = action.payload;
      const result = state.searchResults.find(r => r.id === userId);
      if (result) {
        result.friendship_status = status;
      }
    },
    clearErrors: (state) => {
      state.errors = {
        friends: null,
        search: null,
        sendRequest: null,
      };
    },
  },
  extraReducers: (builder) => {
    // Fetch Friends
    builder
      .addCase(fetchFriends.pending, (state) => {
        state.loading.friends = true;
        state.errors.friends = null;
      })
      .addCase(fetchFriends.fulfilled, (state, action) => {
        state.loading.friends = false;
        state.friends = action.payload;
      })
      .addCase(fetchFriends.rejected, (state, action) => {
        state.loading.friends = false;
        state.errors.friends = action.payload as string;
      });

    // Search Users
    builder
      .addCase(searchUsers.pending, (state) => {
        state.loading.search = true;
        state.errors.search = null;
      })
      .addCase(searchUsers.fulfilled, (state, action) => {
        state.loading.search = false;
        state.searchResults = action.payload;
      })
      .addCase(searchUsers.rejected, (state, action) => {
        state.loading.search = false;
        state.errors.search = action.payload as string;
      });

    // Send Friend Request
    builder
      .addCase(sendFriendRequest.pending, (state) => {
        state.loading.sendRequest = true;
        state.errors.sendRequest = null;
      })
      .addCase(sendFriendRequest.fulfilled, (state) => {
        state.loading.sendRequest = false;
      })
      .addCase(sendFriendRequest.rejected, (state, action) => {
        state.loading.sendRequest = false;
        state.errors.sendRequest = action.payload as string;
      });
  },
});

export const {
  setSearchTerm,
  clearSearchResults,
  setSelectedTab,
  updateSearchResultStatus,
  clearErrors,
} = friendsSlice.actions;

export default friendsSlice.reducer;
```

**`src/redux/slices/friendRequestsSlice.ts`**

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { friendsApi } from '../../services/api/friendsApi';
import { FriendRequest, FriendRequestsResponse } from '../../services/types/friends';

interface FriendRequestsState {
  received: FriendRequest[];
  sent: FriendRequest[];
  loading: {
    fetch: boolean;
    respond: Record<string, boolean>; // requestId -> loading state
  };
  errors: {
    fetch: string | null;
    respond: Record<string, string>; // requestId -> error message
  };
  ui: {
    activeTab: 'received' | 'sent';
  };
}

const initialState: FriendRequestsState = {
  received: [],
  sent: [],
  loading: {
    fetch: false,
    respond: {},
  },
  errors: {
    fetch: null,
    respond: {},
  },
  ui: {
    activeTab: 'received',
  },
};

// Async Thunks
export const fetchFriendRequests = createAsyncThunk(
  'friendRequests/fetchFriendRequests',
  async (_, { rejectWithValue }) => {
    try {
      const requests = await friendsApi.getFriendRequests();
      return requests;
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Failed to fetch friend requests');
    }
  }
);

export const acceptFriendRequest = createAsyncThunk(
  'friendRequests/acceptFriendRequest',
  async (requestId: string, { rejectWithValue }) => {
    try {
      const result = await friendsApi.acceptFriendRequest(requestId);
      return { requestId, ...result };
    } catch (error) {
      return rejectWithValue({ 
        requestId, 
        error: error instanceof Error ? error.message : 'Failed to accept friend request' 
      });
    }
  }
);

export const rejectFriendRequest = createAsyncThunk(
  'friendRequests/rejectFriendRequest',
  async (requestId: string, { rejectWithValue }) => {
    try {
      const result = await friendsApi.rejectFriendRequest(requestId);
      return { requestId, ...result };
    } catch (error) {
      return rejectWithValue({ 
        requestId, 
        error: error instanceof Error ? error.message : 'Failed to reject friend request' 
      });
    }
  }
);

export const cancelFriendRequest = createAsyncThunk(
  'friendRequests/cancelFriendRequest',
  async (requestId: string, { rejectWithValue }) => {
    try {
      const result = await friendsApi.cancelFriendRequest(requestId);
      return { requestId, ...result };
    } catch (error) {
      return rejectWithValue({ 
        requestId, 
        error: error instanceof Error ? error.message : 'Failed to cancel friend request' 
      });
    }
  }
);

const friendRequestsSlice = createSlice({
  name: 'friendRequests',
  initialState,
  reducers: {
    setActiveTab: (state, action: PayloadAction<'received' | 'sent'>) => {
      state.ui.activeTab = action.payload;
    },
    clearErrors: (state) => {
      state.errors.fetch = null;
      state.errors.respond = {};
    },
    clearRequestError: (state, action: PayloadAction<string>) => {
      delete state.errors.respond[action.payload];
    },
  },
  extraReducers: (builder) => {
    // Fetch Friend Requests
    builder
      .addCase(fetchFriendRequests.pending, (state) => {
        state.loading.fetch = true;
        state.errors.fetch = null;
      })
      .addCase(fetchFriendRequests.fulfilled, (state, action) => {
        state.loading.fetch = false;
        state.received = action.payload.received;
        state.sent = action.payload.sent;
      })
      .addCase(fetchFriendRequests.rejected, (state, action) => {
        state.loading.fetch = false;
        state.errors.fetch = action.payload as string;
      });

    // Accept Friend Request
    builder
      .addCase(acceptFriendRequest.pending, (state, action) => {
        state.loading.respond[action.meta.arg] = true;
        delete state.errors.respond[action.meta.arg];
      })
      .addCase(acceptFriendRequest.fulfilled, (state, action) => {
        const { requestId } = action.payload;
        state.loading.respond[requestId] = false;
        // Remove from received requests
        state.received = state.received.filter(req => req.id !== requestId);
      })
      .addCase(acceptFriendRequest.rejected, (state, action) => {
        const { requestId, error } = action.payload as { requestId: string; error: string };
        state.loading.respond[requestId] = false;
        state.errors.respond[requestId] = error;
      });

    // Reject Friend Request
    builder
      .addCase(rejectFriendRequest.pending, (state, action) => {
        state.loading.respond[action.meta.arg] = true;
        delete state.errors.respond[action.meta.arg];
      })
      .addCase(rejectFriendRequest.fulfilled, (state, action) => {
        const { requestId } = action.payload;
        state.loading.respond[requestId] = false;
        // Remove from received requests
        state.received = state.received.filter(req => req.id !== requestId);
      })
      .addCase(rejectFriendRequest.rejected, (state, action) => {
        const { requestId, error } = action.payload as { requestId: string; error: string };
        state.loading.respond[requestId] = false;
        state.errors.respond[requestId] = error;
      });

    // Cancel Friend Request
    builder
      .addCase(cancelFriendRequest.pending, (state, action) => {
        state.loading.respond[action.meta.arg] = true;
        delete state.errors.respond[action.meta.arg];
      })
      .addCase(cancelFriendRequest.fulfilled, (state, action) => {
        const { requestId } = action.payload;
        state.loading.respond[requestId] = false;
        // Remove from sent requests
        state.sent = state.sent.filter(req => req.id !== requestId);
      })
      .addCase(cancelFriendRequest.rejected, (state, action) => {
        const { requestId, error } = action.payload as { requestId: string; error: string };
        state.loading.respond[requestId] = false;
        state.errors.respond[requestId] = error;
      });
  },
});

export const {
  setActiveTab,
  clearErrors,
  clearRequestError,
} = friendRequestsSlice.actions;

export default friendRequestsSlice.reducer;
```

## Custom Hooks

**`src/hooks/useDebounce.ts`**

```typescript
import { useState, useEffect } from 'react';

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}
```

**`src/hooks/useFriends.ts`**

```typescript
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../redux/store';
import { 
  fetchFriends, 
  searchUsers, 
  sendFriendRequest,
  setSearchTerm,
  clearSearchResults,
  setSelectedTab,
  clearErrors 
} from '../redux/slices/friendsSlice';
import { useDebounce } from './useDebounce';

export const useFriends = () => {
  const dispatch = useDispatch<AppDispatch>();
  const friendsState = useSelector((state: RootState) => state.friends);
  
  const debouncedSearchTerm = useDebounce(friendsState.ui.searchTerm, 500);

  // Auto-search when debounced term changes
  useEffect(() => {
    if (debouncedSearchTerm.trim()) {
      dispatch(searchUsers({ query: debouncedSearchTerm }));
    } else {
      dispatch(clearSearchResults());
    }
  }, [debouncedSearchTerm, dispatch]);

  // Load friends on mount
  useEffect(() => {
    if (friendsState.ui.selectedTab === 'friends' && friendsState.friends.length === 0) {
      dispatch(fetchFriends());
    }
  }, [friendsState.ui.selectedTab, friendsState.friends.length, dispatch]);

  const handleSearchTermChange = (term: string) => {
    dispatch(setSearchTerm(term));
  };

  const handleSendFriendRequest = async (receiverId: string) => {
    try {
      await dispatch(sendFriendRequest(receiverId)).unwrap();
      return { success: true };
    } catch (error) {
      return { success: false, error: error as string };
    }
  };

  const handleTabChange = (tab: 'friends' | 'requests' | 'search') => {
    dispatch(setSelectedTab(tab));
    dispatch(clearErrors());
  };

  const refreshFriends = () => {
    dispatch(fetchFriends());
  };

  return {
    ...friendsState,
    handleSearchTermChange,
    handleSendFriendRequest,
    handleTabChange,
    refreshFriends,
  };
};
```

**`src/hooks/useFriendRequests.ts`**

```typescript
import { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState, AppDispatch } from '../redux/store';
import { 
  fetchFriendRequests,
  acceptFriendRequest,
  rejectFriendRequest,
  cancelFriendRequest,
  setActiveTab,
  clearErrors,
  clearRequestError
} from '../redux/slices/friendRequestsSlice';

export const useFriendRequests = () => {
  const dispatch = useDispatch<AppDispatch>();
  const friendRequestsState = useSelector((state: RootState) => state.friendRequests);

  // Load friend requests on mount
  useEffect(() => {
    dispatch(fetchFriendRequests());
  }, [dispatch]);

  const handleAcceptRequest = async (requestId: string) => {
    try {
      await dispatch(acceptFriendRequest(requestId)).unwrap();
      return { success: true };
    } catch (error) {
      return { success: false, error: error as string };
    }
  };

  const handleRejectRequest = async (requestId: string) => {
    try {
      await dispatch(rejectFriendRequest(requestId)).unwrap();
      return { success: true };
    } catch (error) {
      return { success: false, error: error as string };
    }
  };

  const handleCancelRequest = async (requestId: string) => {
    try {
      await dispatch(cancelFriendRequest(requestId)).unwrap();
      return { success: true };
    } catch (error) {
      return { success: false, error: error as string };
    }
  };

  const handleTabChange = (tab: 'received' | 'sent') => {
    dispatch(setActiveTab(tab));
  };

  const handleClearError = (requestId: string) => {
    dispatch(clearRequestError(requestId));
  };

  const refreshRequests = () => {
    dispatch(fetchFriendRequests());
  };

  return {
    ...friendRequestsState,
    handleAcceptRequest,
    handleRejectRequest,
    handleCancelRequest,
    handleTabChange,
    handleClearError,
    refreshRequests,
  };
};
```

## React Components

**`src/components/friends/FriendSearch.tsx`**

```typescript
import React from 'react';
import {
  Box,
  TextField,
  Card,
  CardContent,
  Typography,
  Avatar,
  Button,
  Chip,
  Stack,
  CircularProgress,
  Alert,
  InputAdornment,
} from '@mui/material';
import { Search as SearchIcon, PersonAdd, Check, Schedule } from '@mui/icons-material';
import { useFriends } from '../../hooks/useFriends';
import { UserSearchResult } from '../../services/types/friends';

export const FriendSearch: React.FC = () => {
  const { 
    ui, 
    searchResults, 
    loading, 
    errors,
    handleSearchTermChange, 
    handleSendFriendRequest 
  } = useFriends();

  const handleSendRequest = async (userId: string) => {
    const result = await handleSendFriendRequest(userId);
    if (!result.success) {
      // Error handling is managed by Redux state
      console.error('Failed to send friend request:', result.error);
    }
  };

  const getStatusButton = (user: UserSearchResult) => {
    switch (user.friendship_status) {
      case 'friends':
        return (
          <Button
            variant="outlined"
            startIcon={<Check />}
            disabled
            color="success"
          >
            Friends
          </Button>
        );
      case 'pending_sent':
        return (
          <Button
            variant="outlined"
            startIcon={<Schedule />}
            disabled
            color="warning"
          >
            Request Sent
          </Button>
        );
      case 'pending_received':
        return (
          <Button
            variant="outlined"
            startIcon={<Schedule />}
            disabled
            color="info"
          >
            Request Received
          </Button>
        );
      case 'none':
      default:
        return (
          <Button
            variant="contained"
            startIcon={<PersonAdd />}
            onClick={() => handleSendRequest(user.id)}
            disabled={loading.sendRequest}
          >
            Add Friend
          </Button>
        );
    }
  };

  return (
    <Box>
      <TextField
        fullWidth
        placeholder="Search users by name or email..."
        value={ui.searchTerm}
        onChange={(e) => handleSearchTermChange(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
          endAdornment: loading.search && (
            <InputAdornment position="end">
              <CircularProgress size={20} />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 3 }}
      />

      {errors.search && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errors.search}
        </Alert>
      )}

      {errors.sendRequest && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {errors.sendRequest}
        </Alert>
      )}

      <Stack spacing={2}>
        {searchResults.map((user) => (
          <Card key={user.id} variant="outlined">
            <CardContent>
              <Box display="flex" alignItems="center" gap={2}>
                <Avatar
                  src={user.profile_picture}
                  alt={user.name}
                  sx={{ width: 56, height: 56 }}
                >
                  {user.name.charAt(0).toUpperCase()}
                </Avatar>
                
                <Box flex={1}>
                  <Typography variant="h6">{user.name}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {user.email}
                  </Typography>
                  
                  {user.bio && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      {user.bio}
                    </Typography>
                  )}
                  
                  {user.location && (
                    <Typography variant="caption" color="text.secondary">
                      📍 {user.location.address}
                    </Typography>
                  )}
                  
                  {user.interests && user.interests.length > 0 && (
                    <Box sx={{ mt: 1 }}>
                      {user.interests.slice(0, 3).map((interest) => (
                        <Chip
                          key={interest}
                          label={interest}
                          size="small"
                          sx={{ mr: 0.5, mb: 0.5 }}
                        />
                      ))}
                      {user.interests.length > 3 && (
                        <Chip
                          label={`+${user.interests.length - 3} more`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                    </Box>
                  )}
                </Box>
                
                <Box>{getStatusButton(user)}</Box>
              </Box>
            </CardContent>
          </Card>
        ))}
        
        {ui.searchTerm.trim() && !loading.search && searchResults.length === 0 && (
          <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
            No users found for "{ui.searchTerm}"
          </Typography>
        )}
      </Stack>
    </Box>
  );
};
```

**`src/components/friends/FriendRequestCard.tsx`**

```typescript
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Avatar,
  Button,
  Chip,
  Stack,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Check, Close, Cancel } from '@mui/icons-material';
import { FriendRequest } from '../../services/types/friends';

interface FriendRequestCardProps {
  request: FriendRequest;
  type: 'received' | 'sent';
  onAccept?: (requestId: string) => Promise<{ success: boolean; error?: string }>;
  onReject?: (requestId: string) => Promise<{ success: boolean; error?: string }>;
  onCancel?: (requestId: string) => Promise<{ success: boolean; error?: string }>;
  loading?: boolean;
  error?: string;
}

export const FriendRequestCard: React.FC<FriendRequestCardProps> = ({
  request,
  type,
  onAccept,
  onReject,
  onCancel,
  loading = false,
  error,
}) => {
  const profile = type === 'received' ? request.sender : request.receiver;
  const isReceived = type === 'received';

  const handleAccept = () => {
    if (onAccept) {
      onAccept(request.id);
    }
  };

  const handleReject = () => {
    if (onReject) {
      onReject(request.id);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel(request.id);
    }
  };

  return (
    <Card variant="outlined">
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar
            src={profile.profile_picture}
            alt={profile.name}
            sx={{ width: 56, height: 56 }}
          >
            {profile.name.charAt(0).toUpperCase()}
          </Avatar>
          
          <Box flex={1}>
            <Typography variant="h6">{profile.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {profile.email}
            </Typography>
            
            {profile.bio && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {profile.bio}
              </Typography>
            )}
            
            <Box display="flex" gap={1} mt={1}>
              <Typography variant="caption" color="text.secondary">
                📅 {profile.events_created} events created
              </Typography>
              <Typography variant="caption" color="text.secondary">
                🎯 {profile.events_attended} events attended
              </Typography>
            </Box>
            
            {profile.interests && profile.interests.length > 0 && (
              <Box sx={{ mt: 1 }}>
                {profile.interests.slice(0, 3).map((interest) => (
                  <Chip
                    key={interest}
                    label={interest}
                    size="small"
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
                {profile.interests.length > 3 && (
                  <Chip
                    label={`+${profile.interests.length - 3} more`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
            )}
            
            <Typography variant="caption" color="text.secondary" display="block" mt={1}>
              {isReceived ? 'Sent' : 'Sent to'} {new Date(request.created_at).toLocaleDateString()}
            </Typography>
          </Box>
          
          <Box>
            {loading ? (
              <CircularProgress size={24} />
            ) : (
              <Stack direction="row" spacing={1}>
                {isReceived ? (
                  <>
                    <Button
                      variant="contained"
                      color="success"
                      startIcon={<Check />}
                      onClick={handleAccept}
                      size="small"
                    >
                      Accept
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<Close />}
                      onClick={handleReject}
                      size="small"
                    >
                      Reject
                    </Button>
                  </>
                ) : (
                  <Button
                    variant="outlined"
                    color="warning"
                    startIcon={<Cancel />}
                    onClick={handleCancel}
                    size="small"
                  >
                    Cancel
                  </Button>
                )}
              </Stack>
            )}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
```

**`src/components/friends/FriendCard.tsx`**

```typescript
import React from 'react';
import {
  Card,
  CardContent,
  Box,
  Typography,
  Avatar,
  Chip,
  Button,
} from '@mui/material';
import { Message, Person } from '@mui/icons-material';
import { FriendProfile } from '../../services/types/friends';

interface FriendCardProps {
  friend: FriendProfile;
  onMessage?: (friendId: string) => void;
  onViewProfile?: (friendId: string) => void;
}

export const FriendCard: React.FC<FriendCardProps> = ({
  friend,
  onMessage,
  onViewProfile,
}) => {
  return (
    <Card variant="outlined">
      <CardContent>
        <Box display="flex" alignItems="center" gap={2}>
          <Avatar
            src={friend.profile_picture}
            alt={friend.name}
            sx={{ width: 64, height: 64 }}
          >
            {friend.name.charAt(0).toUpperCase()}
          </Avatar>
          
          <Box flex={1}>
            <Typography variant="h6">{friend.name}</Typography>
            <Typography variant="body2" color="text.secondary">
              {friend.email}
            </Typography>
            
            {friend.bio && (
              <Typography variant="body2" sx={{ mt: 1 }}>
                {friend.bio}
              </Typography>
            )}
            
            {friend.location && (
              <Typography variant="caption" color="text.secondary">
                📍 {friend.location.address}
              </Typography>
            )}
            
            <Box display="flex" gap={2} mt={1}>
              <Typography variant="caption" color="text.secondary">
                📅 {friend.events_created} events created
              </Typography>
              <Typography variant="caption" color="text.secondary">
                🎯 {friend.events_attended} events attended
              </Typography>
            </Box>
            
            {friend.interests && friend.interests.length > 0 && (
              <Box sx={{ mt: 1 }}>
                {friend.interests.slice(0, 4).map((interest) => (
                  <Chip
                    key={interest}
                    label={interest}
                    size="small"
                    sx={{ mr: 0.5, mb: 0.5 }}
                  />
                ))}
                {friend.interests.length > 4 && (
                  <Chip
                    label={`+${friend.interests.length - 4} more`}
                    size="small"
                    variant="outlined"
                  />
                )}
              </Box>
            )}
            
            <Typography variant="caption" color="text.secondary" display="block" mt={1}>
              Friends since {new Date(friend.created_at || '').toLocaleDateString()}
            </Typography>
          </Box>
          
          <Box>
            <Box display="flex" flexDirection="column" gap={1}>
              {onViewProfile && (
                <Button
                  variant="outlined"
                  startIcon={<Person />}
                  onClick={() => onViewProfile(friend.id)}
                  size="small"
                >
                  Profile
                </Button>
              )}
              {onMessage && (
                <Button
                  variant="contained"
                  startIcon={<Message />}
                  onClick={() => onMessage(friend.id)}
                  size="small"
                >
                  Message
                </Button>
              )}
            </Box>
          </Box>
        </Box>
      </CardContent>
    </Card>
  );
};
```

## Main Pages

**`src/pages/Friends.tsx`**

```typescript
import React from 'react';
import {
  Container,
  Typography,
  Box,
  Tabs,
  Tab,
  Badge,
  CircularProgress,
  Alert,
  Stack,
  Button,
} from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { useFriends } from '../hooks/useFriends';
import { useFriendRequests } from '../hooks/useFriendRequests';
import { FriendCard } from '../components/friends/FriendCard';
import { FriendSearch } from '../components/friends/FriendSearch';
import { FriendRequestCard } from '../components/friends/FriendRequestCard';

export const Friends: React.FC = () => {
  const friendsState = useFriends();
  const friendRequestsState = useFriendRequests();

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    const tabs = ['friends', 'search', 'requests'] as const;
    friendsState.handleTabChange(tabs[newValue]);
  };

  const handleViewProfile = (friendId: string) => {
    // Navigate to user profile page
    console.log('View profile:', friendId);
  };

  const handleMessage = (friendId: string) => {
    // Navigate to messages or open chat
    console.log('Message friend:', friendId);
  };

  const tabIndex = friendsState.ui.selectedTab === 'friends' ? 0 
    : friendsState.ui.selectedTab === 'search' ? 1 : 2;

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Friends
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={tabIndex} onChange={handleTabChange}>
          <Tab 
            label={
              <Badge badgeContent={friendsState.friends.length} color="primary">
                My Friends
              </Badge>
            } 
          />
          <Tab label="Search Users" />
          <Tab 
            label={
              <Badge 
                badgeContent={friendRequestsState.received.length} 
                color="error"
              >
                Requests
              </Badge>
            } 
          />
        </Tabs>
      </Box>

      {/* Friends List Tab */}
      {friendsState.ui.selectedTab === 'friends' && (
        <Box>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Your Friends ({friendsState.friends.length})
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={friendsState.refreshFriends}
              disabled={friendsState.loading.friends}
            >
              Refresh
            </Button>
          </Box>

          {friendsState.loading.friends ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : friendsState.errors.friends ? (
            <Alert severity="error">{friendsState.errors.friends}</Alert>
          ) : friendsState.friends.length === 0 ? (
            <Box textAlign="center" py={8}>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                No friends yet
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Search for users and send friend requests to start building your network!
              </Typography>
            </Box>
          ) : (
            <Stack spacing={2}>
              {friendsState.friends.map((friend) => (
                <FriendCard
                  key={friend.id}
                  friend={friend}
                  onViewProfile={handleViewProfile}
                  onMessage={handleMessage}
                />
              ))}
            </Stack>
          )}
        </Box>
      )}

      {/* Search Tab */}
      {friendsState.ui.selectedTab === 'search' && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Find New Friends
          </Typography>
          <FriendSearch />
        </Box>
      )}

      {/* Friend Requests Tab */}
      {friendsState.ui.selectedTab === 'requests' && (
        <Box>
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
            <Tabs 
              value={friendRequestsState.ui.activeTab === 'received' ? 0 : 1}
              onChange={(_, newValue) => 
                friendRequestsState.handleTabChange(newValue === 0 ? 'received' : 'sent')
              }
            >
              <Tab 
                label={
                  <Badge badgeContent={friendRequestsState.received.length} color="error">
                    Received
                  </Badge>
                } 
              />
              <Tab 
                label={
                  <Badge badgeContent={friendRequestsState.sent.length} color="warning">
                    Sent
                  </Badge>
                } 
              />
            </Tabs>
          </Box>

          {friendRequestsState.loading.fetch ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : friendRequestsState.errors.fetch ? (
            <Alert severity="error">{friendRequestsState.errors.fetch}</Alert>
          ) : (
            <Stack spacing={2}>
              {friendRequestsState.ui.activeTab === 'received' && (
                <>
                  {friendRequestsState.received.length === 0 ? (
                    <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
                      No pending friend requests
                    </Typography>
                  ) : (
                    friendRequestsState.received.map((request) => (
                      <FriendRequestCard
                        key={request.id}
                        request={request}
                        type="received"
                        onAccept={friendRequestsState.handleAcceptRequest}
                        onReject={friendRequestsState.handleRejectRequest}
                        loading={friendRequestsState.loading.respond[request.id]}
                        error={friendRequestsState.errors.respond[request.id]}
                      />
                    ))
                  )}
                </>
              )}

              {friendRequestsState.ui.activeTab === 'sent' && (
                <>
                  {friendRequestsState.sent.length === 0 ? (
                    <Typography variant="body1" color="text.secondary" textAlign="center" py={4}>
                      No pending sent requests
                    </Typography>
                  ) : (
                    friendRequestsState.sent.map((request) => (
                      <FriendRequestCard
                        key={request.id}
                        request={request}
                        type="sent"
                        onCancel={friendRequestsState.handleCancelRequest}
                        loading={friendRequestsState.loading.respond[request.id]}
                        error={friendRequestsState.errors.respond[request.id]}
                      />
                    ))
                  )}
                </>
              )}
            </Stack>
          )}
        </Box>
      )}
    </Container>
  );
};
```

## Cache Invalidation Strategy

**`src/utils/friendsHelpers.ts`**

```typescript
import { AppDispatch } from '../redux/store';
import { fetchFriends } from '../redux/slices/friendsSlice';
import { fetchFriendRequests } from '../redux/slices/friendRequestsSlice';

export class FriendsCacheManager {
  private dispatch: AppDispatch;

  constructor(dispatch: AppDispatch) {
    this.dispatch = dispatch;
  }

  // Invalidate all friend-related caches
  invalidateAll() {
    this.dispatch(fetchFriends());
    this.dispatch(fetchFriendRequests());
  }

  // Invalidate friends list only
  invalidateFriends() {
    this.dispatch(fetchFriends());
  }

  // Invalidate friend requests only
  invalidateFriendRequests() {
    this.dispatch(fetchFriendRequests());
  }

  // Call this after sending a friend request
  onFriendRequestSent() {
    this.dispatch(fetchFriendRequests());
  }

  // Call this after accepting/rejecting a friend request
  onFriendRequestResponded() {
    this.invalidateAll(); // Both friends list and requests change
  }

  // Call this after cancelling a friend request
  onFriendRequestCancelled() {
    this.dispatch(fetchFriendRequests());
  }
}

// Utility functions for cache invalidation triggers
export const triggerCacheInvalidation = (
  dispatch: AppDispatch,
  action: 'send' | 'accept' | 'reject' | 'cancel'
) => {
  const cacheManager = new FriendsCacheManager(dispatch);
  
  switch (action) {
    case 'send':
      cacheManager.onFriendRequestSent();
      break;
    case 'accept':
    case 'reject':
      cacheManager.onFriendRequestResponded();
      break;
    case 'cancel':
      cacheManager.onFriendRequestCancelled();
      break;
  }
};
```

## Testing Strategy

**`src/components/friends/__tests__/FriendSearch.test.tsx`**

```typescript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { FriendSearch } from '../FriendSearch';
import friendsReducer from '../../../redux/slices/friendsSlice';
import { friendsApi } from '../../../services/api/friendsApi';

// Mock the API
jest.mock('../../../services/api/friendsApi');
const mockedFriendsApi = friendsApi as jest.Mocked<typeof friendsApi>;

const createTestStore = () => {
  return configureStore({
    reducer: {
      friends: friendsReducer,
    },
  });
};

const renderWithStore = (component: React.ReactElement) => {
  const store = createTestStore();
  return render(
    <Provider store={store}>
      {component}
    </Provider>
  );
};

describe('FriendSearch', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders search input', () => {
    renderWithStore(<FriendSearch />);
    expect(screen.getByPlaceholderText(/search users/i)).toBeInTheDocument();
  });

  it('searches users when typing', async () => {
    const mockSearchResults = [
      {
        id: 'user1@example.com',
        name: 'John Doe',
        email: 'user1@example.com',
        friendship_status: 'none' as const,
      },
    ];

    mockedFriendsApi.searchUsers.mockResolvedValue(mockSearchResults);

    renderWithStore(<FriendSearch />);
    
    const searchInput = screen.getByPlaceholderText(/search users/i);
    fireEvent.change(searchInput, { target: { value: 'john' } });

    await waitFor(() => {
      expect(mockedFriendsApi.searchUsers).toHaveBeenCalledWith('john', 20);
    }, { timeout: 1000 }); // Account for debounce
  });

  it('shows Add Friend button for users with no relationship', async () => {
    const mockSearchResults = [
      {
        id: 'user1@example.com',
        name: 'John Doe',
        email: 'user1@example.com',
        friendship_status: 'none' as const,
      },
    ];

    mockedFriendsApi.searchUsers.mockResolvedValue(mockSearchResults);

    renderWithStore(<FriendSearch />);
    
    const searchInput = screen.getByPlaceholderText(/search users/i);
    fireEvent.change(searchInput, { target: { value: 'john' } });

    await waitFor(() => {
      expect(screen.getByText('Add Friend')).toBeInTheDocument();
    });
  });

  it('sends friend request when Add Friend is clicked', async () => {
    const mockSearchResults = [
      {
        id: 'user1@example.com',
        name: 'John Doe',
        email: 'user1@example.com',
        friendship_status: 'none' as const,
      },
    ];

    mockedFriendsApi.searchUsers.mockResolvedValue(mockSearchResults);
    mockedFriendsApi.sendFriendRequest.mockResolvedValue({
      message: 'Friend request sent successfully',
      request_id: 'test-123',
    });

    renderWithStore(<FriendSearch />);
    
    const searchInput = screen.getByPlaceholderText(/search users/i);
    fireEvent.change(searchInput, { target: { value: 'john' } });

    await waitFor(() => {
      expect(screen.getByText('Add Friend')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Add Friend'));

    await waitFor(() => {
      expect(mockedFriendsApi.sendFriendRequest).toHaveBeenCalledWith({
        receiver_id: 'user1@example.com',
      });
    });
  });
});
```

## Performance Optimizations

**Memoization and Optimization Patterns:**

```typescript
// In FriendCard.tsx - Memoize expensive renders
export const FriendCard = React.memo<FriendCardProps>(({
  friend,
  onMessage,
  onViewProfile,
}) => {
  // Component implementation
}, (prevProps, nextProps) => {
  // Custom comparison for better performance
  return (
    prevProps.friend.id === nextProps.friend.id &&
    prevProps.friend.name === nextProps.friend.name &&
    prevProps.friend.profile_picture === nextProps.friend.profile_picture
  );
});

// In hooks - Memoize selectors
export const useFriends = () => {
  const friendsState = useSelector((state: RootState) => state.friends, shallowEqual);
  
  const sortedFriends = useMemo(() => {
    return [...friendsState.friends].sort((a, b) => a.name.localeCompare(b.name));
  }, [friendsState.friends]);

  // Rest of hook implementation
};
```

## Error Boundary

**`src/components/ErrorBoundary.tsx`**

```typescript
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Alert, Button, Box, Typography } from '@mui/material';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Friends system error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <Box p={3}>
          <Alert severity="error">
            <Typography variant="h6" gutterBottom>
              Something went wrong with the Friends system
            </Typography>
            <Typography variant="body2" gutterBottom>
              {this.state.error?.message || 'An unexpected error occurred'}
            </Typography>
            <Button 
              variant="outlined" 
              onClick={() => this.setState({ hasError: false })}
              sx={{ mt: 2 }}
            >
              Try Again
            </Button>
          </Alert>
        </Box>
      );
    }

    return this.props.children;
  }
}
```

## Usage Example

**`src/App.tsx`**

```typescript
import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { store } from './redux/store';
import { theme } from './theme';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Friends } from './pages/Friends';

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <ErrorBoundary>
            <Routes>
              <Route path="/friends" element={<Friends />} />
              {/* Other routes */}
            </Routes>
          </ErrorBoundary>
        </Router>
      </ThemeProvider>
    </Provider>
  );
}

export default App;
```

## Deployment Notes

1. **Environment Variables:**
   ```env
   REACT_APP_API_URL=https://api.sahana.com
   REACT_APP_DEBOUNCE_DELAY=500
   ```

2. **Build Optimization:**
   ```json
   // vite.config.ts
   export default defineConfig({
     build: {
       rollupOptions: {
         output: {
           manualChunks: {
             friends: ['./src/pages/Friends.tsx', './src/components/friends/index.ts'],
           },
         },
       },
     },
   });
   ```

3. **Performance Monitoring:**
   - Monitor API response times for search queries
   - Track friend request success/failure rates
   - Monitor cache hit rates and invalidation frequency

This comprehensive frontend implementation provides a complete, production-ready Friends system that integrates seamlessly with the backend APIs we built earlier!
