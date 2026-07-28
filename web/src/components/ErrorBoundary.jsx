import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
          <div className="max-w-md text-center">
            <h1 className="text-2xl font-bold text-gray-900 mb-2">Something went wrong</h1>
            <p className="text-gray-500 mb-4">Please refresh the page or try again later.</p>
            <button onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="bg-purple-700 text-white px-6 py-2 rounded-lg">
              Refresh
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
