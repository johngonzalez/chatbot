import React from 'react';

const Header = () => {
  return (
<div className="bg-blue-900 text-white text-center py-4">
  <center>
    <div className="flex items-center justify-center">
      <a href="https://bancodebogota.com" target="_blank" rel="noopener noreferrer">
        <img
          src="https://static.wikia.nocookie.net/logopedia/images/7/7b/Banco_de_bogota_symbol_2008.png"
          alt="Logo App Banco de Bogotá"
          width={50}
          className="ml-2"
        />
      </a>
      <span className="text-2xl font-semibold ml-2">Chatea con Clara</span>
    </div>
  </center>
</div>
  );
};

export default Header;