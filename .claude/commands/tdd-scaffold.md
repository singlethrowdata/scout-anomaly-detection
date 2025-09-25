Create a complete test scaffold for feature: $ARGUMENTS

## 1️⃣ Read Feature Requirements
Extract from CLAUDE.local.md:
- All requirements [R#] for this feature
- Success criteria
- Boundaries/constraints
- Performance requirements

## 2️⃣ Generate Comprehensive Test File

### JavaScript Example:
```javascript
// tests/[feature].test.js
import { describe, test, expect, beforeEach, afterEach } from '@jest/globals';
import { Feature } from '../src/[feature]';

describe('[Feature Name]', () => {
  let instance;
  
  beforeEach(() => {
    // Setup fresh instance for each test
    instance = new Feature();
    // Setup mocks/fixtures
  });
  
  afterEach(() => {
    // Cleanup
  });
  
  describe('Requirement [R1]: [Description]', () => {
    test('should [expected behavior for happy path]', () => {
      // Arrange
      const input = {};
      
      // Act
      const result = instance.method(input);
      
      // Assert
      expect(result).toBe(expected);
    });
    
    test('should handle [edge case]', () => {
      // Test boundary condition
    });
    
    test('should throw error when [invalid input]', () => {
      // Test error handling
      expect(() => instance.method(invalid)).toThrow('Expected error');
    });
  });
  
  describe('Requirement [R2]: [Description]', () => {
    // Tests for R2
  });
  
  describe('Performance Requirements', () => {
    test('should complete within 200ms', () => {
      const start = Date.now();
      instance.processLargeDataset(testData);
      const duration = Date.now() - start;
      expect(duration).toBeLessThan(200);
    });
  });
  
  describe('Integration Tests', () => {
    test('should work with [other feature]', () => {
      // Test integration points
    });
  });
});
```

### Python Example:
```python
# tests/test_[feature].py
import pytest
from unittest.mock import Mock, patch
from src.[feature] import Feature

class TestFeature:
    """Tests for [Feature Name]"""
    
    @pytest.fixture
    def instance(self):
        """Create fresh instance for each test"""
        return Feature()
    
    @pytest.fixture
    def mock_database(self):
        """Mock database for testing"""
        with patch('src.[feature].database') as mock:
            yield mock
    
    # Requirement [R1]: [Description]
    def test_happy_path_for_r1(self, instance):
        """Should [expected behavior]"""
        # Arrange
        input_data = {}
        
        # Act
        result = instance.method(input_data)
        
        # Assert
        assert result == expected
    
    def test_edge_case_for_r1(self, instance):
        """Should handle [edge case]"""
        # Implementation
        pass
    
    def test_error_handling_for_r1(self, instance):
        """Should raise error for invalid input"""
        with pytest.raises(ValueError, match="Expected error"):
            instance.method(invalid_input)
    
    # Requirement [R2]: [Description]
    def test_requirement_r2(self, instance):
        """Tests for R2"""
        pass
    
    # Performance Tests
    def test_performance_requirement(self, instance, benchmark):
        """Should complete within 200ms"""
        result = benchmark(instance.process_large_dataset, test_data)
        assert benchmark.stats['mean'] < 0.2  # 200ms
    
    # Integration Tests
    def test_integration_with_other_feature(self, instance, mock_database):
        """Should integrate with [other feature]"""
        # Test integration
        pass
```

## 3️⃣ Create Test Fixtures/Mocks

### fixtures/[feature]_fixtures.js or .py
```javascript
// Test data that represents real-world scenarios
export const validUserData = {
  email: 'test@example.com',
  password: 'SecurePass123!'
};

export const invalidUserData = {
  email: 'not-an-email',
  password: '123'  // Too weak
};

export const edgeCaseData = {
  email: 'a'.repeat(255) + '@test.com',  // Max length
  password: '🦄Unicode!123'  // Unicode characters
};
```

## 4️⃣ Generate Test Matrix

```markdown
## Test Coverage Matrix for [Feature]

| Requirement | Happy Path | Edge Cases | Error Cases | Performance | Integration |
|------------|------------|------------|-------------|-------------|-------------|
| [R1]       | ✅         | ✅         | ✅          | N/A         | ✅          |
| [R2]       | ✅         | ✅         | ✅          | ✅          | N/A         |
| [R3]       | ✅         | ✅         | ✅          | N/A         | ✅          |

Total Tests: X
Estimated Coverage: >80%
```

## 5️⃣ Include Helpful Comments

Each test should have:
```javascript
test('should [behavior]', () => {
  // This test validates requirement [R1] from WBS
  // Testing that when X happens, Y is the result
  // This ensures [business value/reason]
  
  // ... test implementation
});
```

## 6️⃣ Create Test Commands

Add to package.json or project config:
```json
{
  "scripts": {
    "test:[feature]": "jest tests/[feature].test.js",
    "test:[feature]:watch": "jest --watch tests/[feature].test.js",
    "test:[feature]:coverage": "jest --coverage tests/[feature].test.js"
  }
}
```

## 7️⃣ Output Summary

```
📝 TEST SCAFFOLD GENERATED
━━━━━━━━━━━━━━━━━━━━━━━
Feature: [Name]
File: tests/test_[feature].py/js
Tests Created: X
Requirements Covered: [R1], [R2], [R3]

Test Categories:
✅ Happy Path: X tests
✅ Edge Cases: Y tests
✅ Error Handling: Z tests
✅ Performance: N tests
✅ Integration: M tests

Next Steps:
1. Run tests to verify they all fail
2. Implement feature code
3. Make tests pass one by one
4. Refactor once all green

Run with: npm test:[feature]
```

The scaffold is complete and ready for TDD implementation!
