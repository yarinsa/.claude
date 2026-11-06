import axios from 'axios';
import React, { useEffect } from 'react';
import { useState } from 'react';

export const ResouceLoader = ({ resouceUrl, resourceName, children }) => {
  const [resource, setResource] = useState(null);

  useEffect(() => {
    (async () => {
      const response = await axios.get(resouceUrl);
      setResource(response.data);
    })();
  }, [resouceUrl]);

  return (
    <>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { [resourceName]: resource });
        }
        return child;
      })}
    </>
  );
};
