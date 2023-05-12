import React from 'react';

const Header = () => {
  return (
<div className="bg-gray-700 text-white text-center py-4">
  <center>
    <div className="flex items-center justify-center">
      <a href="https://bancodebogota.com" target="_blank" rel="noopener noreferrer">
        <img
          src="https://upload.wikimedia.org/wikipedia/commons/2/23/Logo_2.0_banco_de_bogota.png"
          alt="Logo App Banco de Bogotá"
          width={200}
          className="ml-2"
        />
      </a>
      <span className="text-2xl font-semibold ml-2">Pregúntale a Clara</span>
    </div>
  </center>
</div>
  );
};

export default Header;