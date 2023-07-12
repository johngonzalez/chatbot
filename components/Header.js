import React from 'react';

const Header = () => {
  return (
<div className="bg-purple-900 text-white text-center py-4">
  <center>
    <div className="flex items-center justify-center">
      <a href="https://bancodebogota.com" target="_blank" rel="noopener noreferrer">
        <img
          src="https://www.adldigitallab.com/assets/images/logo.png"
          alt="Logo ADL"
          width={50}
          className="ml-2"
        />
      </a>
      <span className="text-2xl font-semibold ml-2">Chatea con Linguo</span>
    </div>
  </center>
</div>
  );
};

export default Header;