# Troubleshooting Guide

Common issues and solutions for the Sahana Backend.

## Installation Issues

### Python Environment Problems

**Issue**: `ImportError` or module not found errors

**Solutions**:

- Ensure virtual environment is activated: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.10+)
- Clear pip cache: `pip cache purge`

### Virtual Environment Issues

**Issue**: Virtual environment not working properly

**Solutions**:
```bash
# Delete existing venv and recreate
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Firebase Configuration

### Firebase Credentials Not Found

**Issue**: `FileNotFoundError: firebase_cred.json`

**Solutions**:

- Ensure `firebase_cred.json` is in the project root
- Check file permissions: `chmod 644 firebase_cred.json`
- Verify environment variable: `echo $GOOGLE_APPLICATION_CREDENTIALS`

### Firebase Authentication Error

**Issue**: `FirebaseError: Invalid credentials`

**Solutions**:

- Download fresh Firebase credentials from console
- Ensure the service account has proper permissions
- Check if the Firebase project is active

### Firestore Permission Denied

**Issue**: `PermissionDenied: Missing or insufficient permissions`

**Solutions**:

- Check Firestore security rules
- Ensure service account has Firestore permissions
- Verify project ID matches in credentials

## Server Startup Issues

### Port Already in Use

**Issue**: `OSError: [Errno 48] Address already in use`

**Solutions**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### Environment Variables Not Loading

**Issue**: Environment variables from `.env` not working

**Solutions**:

- Check `.env` file format (no spaces around =)
- Ensure `.env` is in the project root
- Verify python-dotenv is installed
- Check if variables are being loaded in `config.py`

## API Request Issues

### CORS Errors

**Issue**: Cross-origin request blocked

**Solutions**:

- Check CORS configuration in `main.py`
- Add frontend domain to allowed origins
- Ensure proper headers are included

### Authentication Token Issues

**Issue**: `401 Unauthorized` errors

**Solutions**:

- Check token format: `Authorization: Bearer <token>`
- Verify token hasn't expired
- Ensure JWT secret keys match
- Test with a fresh login token

### Request Validation Errors

**Issue**: `422 Unprocessable Entity`

**Solutions**:

- Check request body format and required fields
- Verify JSON syntax
- Ensure Content-Type is `application/json`
- Review API documentation for correct format

## Database Issues

### Firestore Connection Timeout

**Issue**: Requests to Firestore timing out

**Solutions**:

- Check internet connection
- Verify Firebase project is active
- Check for Firebase service outages
- Increase timeout settings

### Document Not Found Errors

**Issue**: Firestore documents not found

**Solutions**:

- Verify collection and document IDs
- Check document creation logic
- Use Firestore console to inspect data
- Ensure proper error handling

## Development Issues

### Hot Reload Not Working

**Issue**: Changes not reflected when using `--reload`

**Solutions**:

- Restart the server manually
- Check file permissions
- Ensure files are saved properly
- Try using `--reload-dir app`

### Import Errors

**Issue**: Circular imports or import errors

**Solutions**:

- Check import statements for circular dependencies
- Use absolute imports: `from app.models import Event`
- Verify `__init__.py` files exist in packages

## Testing Issues

### Tests Failing

**Issue**: Unit tests not passing

**Solutions**:

- Ensure test database is properly set up
- Check test environment variables
- Run tests individually to isolate issues
- Clear test data between runs

## Performance Issues

### Slow API Responses

**Issue**: API endpoints responding slowly

**Solutions**:

- Check database query efficiency
- Review Firestore indexes
- Monitor server resources
- Implement pagination for large datasets
- Use caching for frequently accessed data

### Memory Usage High

**Issue**: High memory consumption

**Solutions**:

- Monitor for memory leaks
- Implement proper connection pooling
- Review large data operations
- Use pagination for bulk operations

## Docker Issues

### Container Build Failures

**Issue**: Docker build fails

**Solutions**:

- Check Dockerfile syntax
- Ensure all required files are included
- Review .dockerignore file
- Clear Docker build cache: `docker system prune -a`

### Container Runtime Issues

**Issue**: Container exits immediately

**Solutions**:

- Check container logs: `docker logs <container_name>`
- Verify environment variables are set
- Ensure firebase credentials are mounted
- Check port binding conflicts

## Logging and Debugging

### Enable Debug Logging

Add to your development environment:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Application Logs

```bash
# View recent logs
tail -f app.log

# Search for specific errors
grep "ERROR" app.log
```

### Monitor API Requests

Use the interactive documentation at `http://localhost:8000/docs` to test endpoints.

## Common Error Messages

### "uvicorn command not found"

**Solution**: Ensure uvicorn is installed and virtual environment is activated

```bash
pip install uvicorn
source venv/bin/activate
```

### "No module named 'app'"

**Solution**: Run uvicorn from project root directory where `app` folder is located

### "Firebase project not found"

**Solution**: Check project ID in Firebase credentials matches your Firebase console

### "Token verification failed"

**Solution**: Check JWT secret key configuration and token format

## Getting Help

If you're still experiencing issues:

1. Check the [GitHub Issues](https://github.com/your-repo/issues)
2. Review the [API Documentation](api/overview.md)
3. Enable debug logging to get more details
4. Create a minimal reproduction case
5. Include relevant error messages and logs when asking for help

## Useful Commands

```bash
# Check Python and pip versions
python --version
pip --version

# List installed packages
pip list

# Check virtual environment
which python

# Test Firebase connection
python -c "import firebase_admin; print('Firebase imported successfully')"

# Validate JSON files
python -m json.tool firebase_cred.json

# Check port usage
netstat -tulpn | grep :8000

# Check system resources
top
ps aux | grep uvicorn
```
