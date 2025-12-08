import React from 'react';

const LoadingSpinner = ({ size = 'md', className = '' }) => {
    const sizes = {
        sm: 'w-4 h-4 border-2',
        md: 'w-8 h-8 border-3',
        lg: 'w-12 h-12 border-4',
        xl: 'w-16 h-16 border-4',
    };

    return (
        <div
            className={`spinner ${sizes[size]} border-primary-500 border-t-transparent rounded-full ${className}`}
        ></div>
    );
};

export default LoadingSpinner;
