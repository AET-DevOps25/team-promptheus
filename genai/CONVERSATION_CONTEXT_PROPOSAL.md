# Conversation Context Implementation Proposal

## Overview

This proposal introduces conversation context to the GenAI question-answering service, allowing users to have continuous conversations where follow-up questions can reference previous Q&As in the same session.

## Problem Statement

Currently, each question is answered in isolation without knowledge of previous questions or answers. This creates a poor user experience when users want to:
- Ask follow-up questions
- Drill down into specific topics
- Have a natural conversation flow
- Reference previous answers

## Proposed Solution

### Core Components

#### 1. New Data Models

**ConversationTurn**: Represents a single Q&A exchange
```python
class ConversationTurn(BaseModel):
    question: str
    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    asked_at: datetime
    response_time_ms: int
```

**ConversationThread**: Manages a complete conversation
```python
class ConversationThread(BaseModel):
    conversation_id: str  # UUIDv7
    user: str
    week: str
    turns: List[ConversationTurn] = Field(default_factory=list)
    created_at: datetime
    last_activity_at: datetime
    
    def add_turn(self, question: str, answer: str, confidence: float, response_time_ms: int) -> None
    def get_recent_turns(self, max_turns: int = 5) -> List[ConversationTurn]
```

#### 2. Enhanced Question Context

Extended `QuestionContext` with conversation features:
```python
class QuestionContext(BaseModel):
    # Existing fields...
    conversation_id: Optional[str] = None  # Links questions in a conversation
    max_conversation_history: int = 5      # Max previous Q&As to include
```

#### 3. Service Layer Changes

**QuestionAnsweringService** enhancements:
- `conversations_store`: Dict[str, ConversationThread] - stores active conversations
- `user_conversations`: Dict[str, str] - maps user:week to conversation_id
- `_get_or_create_conversation()` - manages conversation lifecycle
- Enhanced `_generate_agentic_answer()` - includes conversation history in LLM prompts

## Key Features

### 1. Automatic Conversation Management
- **Per user/week**: Each user-week combination gets one conversation thread
- **Conversation linking**: Questions can explicitly reference a conversation ID
- **Auto-creation**: New conversations created automatically when needed

### 2. Context-Aware LLM Prompts
The LLM system prompt now includes:
- Previous conversation turns (configurable limit)
- Instructions to reference previous Q&As when relevant
- Guidance to maintain conversational flow

### 3. Conversation Storage & Retrieval
- In-memory storage (can be extended to persistent storage)
- Conversation threads track all turns with metadata
- Efficient lookup by conversation ID or user/week

### 4. API Endpoints

**Enhanced existing endpoint**:
```
POST /users/{username}/weeks/{week_id}/questions
```
- Now accepts `conversation_id` in context
- Returns responses with `conversation_id`

**New conversation endpoints**:
```
GET /users/{username}/weeks/{week_id}/conversations
GET /conversations/{conversation_id}
```

## Usage Examples

### Basic Conversation Flow
```python
# Question 1 - creates new conversation
response1 = ask_question("What did I work on this week?")
conversation_id = response1.conversation_id

# Question 2 - continues conversation
response2 = ask_question(
    "What challenges did I face?", 
    conversation_id=conversation_id
)
# This answer can now reference the first question/answer
```

### API Usage
```json
{
  "question": "What were the main blockers?",
  "context": {
    "conversation_id": "01234567-89ab-cdef-0123-456789abcdef",
    "max_conversation_history": 5,
    "reasoning_depth": "detailed"
  }
}
```

## Benefits

### For Users
- **Natural conversation flow**: Ask follow-up questions naturally
- **Contextual answers**: Responses reference previous discussion
- **Progressive exploration**: Drill down into topics incrementally
- **Reduced repetition**: No need to re-explain context

### For Developers  
- **Backward compatible**: Existing API calls work unchanged
- **Optional feature**: Conversation context is opt-in
- **Flexible configuration**: Controllable history length
- **Clear separation**: Conversation logic isolated in service layer

## Implementation Details

### Memory Management
- **Conversation cleanup**: Could add TTL or size limits
- **Storage scaling**: Easy to extend to persistent storage (Redis, DB)
- **Context limits**: Configurable history length prevents token overflow

### LLM Integration
- **Conversation history**: Added to system prompt for context
- **Token management**: History is summarized/truncated as needed
- **Fallback handling**: Works gracefully when LLM fails

### Error Handling
- **Conversation mismatch**: Validates conversation belongs to user/week
- **Missing conversations**: Creates new ones when needed
- **Service failures**: Degrades gracefully to stateless mode

## Future Extensions

### Persistence Layer
- Database storage for conversation history
- Cross-session conversation continuity
- Conversation search and analytics

### Advanced Features
- **Conversation summarization**: Compress long conversations
- **Multi-week conversations**: Link conversations across weeks
- **Conversation templates**: Pre-defined conversation flows
- **Conversation export**: Download conversation history

### Analytics
- Conversation engagement metrics
- Question progression patterns
- Context effectiveness measurement

## Testing Strategy

### Unit Tests
- ConversationThread operations
- Service conversation management
- LLM prompt generation with context

### Integration Tests
- End-to-end conversation flows
- API endpoint functionality
- Error handling scenarios

### Example Scenarios
- Multi-turn conversations
- Conversation recovery
- Context limit behavior

## Migration Path

1. **Phase 1**: Deploy with conversation context (backward compatible)
2. **Phase 2**: Add persistence layer
3. **Phase 3**: Enhanced conversation features
4. **Phase 4**: Analytics and optimization

## Technical Considerations

### Performance
- In-memory storage is fast but limited by memory
- Conversation history adds to LLM token usage
- Context retrieval is O(1) with hash maps

### Scalability
- Per-service-instance storage limits horizontal scaling
- Should move to shared storage (Redis) for production
- Consider conversation archival for old conversations

### Security
- Conversation access control (user/week validation)
- Conversation ID generation (UUIDv7 for security)
- Data privacy considerations for conversation storage

## Conclusion

This implementation provides a solid foundation for conversation context while maintaining backward compatibility. It enables natural conversational Q&A without disrupting existing functionality, and provides a clear path for future enhancements.

The proposed solution balances simplicity with functionality, making it easy to deploy and extend as needed. 