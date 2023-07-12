import React, { useRef, useEffect } from 'react'

const InputBar = ({ input, setInput, handleKeyDown, handleSubmit }) => {
  const inputRef = useRef(null)

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
    }
  }, [input])

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex items-center px-4 py-2 justify-center md:px-4 md:py-4">
        <div className="w-full md:w-1/2 max-w-xl flex items-center">
          <textarea
            ref={inputRef}
            rows="1"
            placeholder="Cuál es la vigencia de los beneficios?"
            className="flex-1 p-2 border rounded-lg focus:outline-none focus:ring focus:border-purple-900 resize-none overflow-hidden bg-gray-100 text-gray-700"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            type="submit"
            className="ml-2 px-2 py-1 rounded-lg bg-gray-100 text-purple-900 focus:outline-none hover:bg-gray-300 md:ml-4 md:px-4 md:py-2"
          >
            Envía
          </button>
        </div>
      </form>
      <div className="pb-2 text-center text-xs text-gray-200 md:pb-4">
        En desarrollo. Las respuestas podrían no ser correctas. Última actualización 2023-05-12
      </div>
    </div>
  )
}

export default InputBar