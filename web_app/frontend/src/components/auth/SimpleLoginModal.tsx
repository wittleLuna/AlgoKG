import React from 'react';
import { createPortal } from 'react-dom';

interface SimpleLoginModalProps {
  visible: boolean;
  onClose: () => void;
}

const SimpleLoginModal: React.FC<SimpleLoginModalProps> = ({ visible, onClose }) => {
  console.log('SimpleLoginModal render:', visible);
  
  if (!visible) return null;

  const modalContent = (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.8)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 99999
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: 'white',
          padding: '40px',
          borderRadius: '8px',
          minWidth: '300px',
          textAlign: 'center'
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2>登录测试</h2>
        <p>这是一个测试模态框</p>
        <button onClick={onClose} style={{ padding: '10px 20px', marginTop: '20px' }}>
          关闭
        </button>
      </div>
    </div>
  );

  return createPortal(modalContent, document.body);
};

export default SimpleLoginModal;
