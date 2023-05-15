## Deployment

Unzip zcta.tar.xz into the same folder and delete the archive.
Follow the instructions for deployment.

https://learn.microsoft.com/en-us/azure/azure-functions/functions-deployment-technologies

## Basic usage:

### BaseUrl

    {host}/api/static-maps?

### Query Parameters

| Parametr | Type              | Default        | Required |
| -------- | ----------------- | -------------- | -------- |
| color    | HEX               | 0E8BDE         | []       |
| style    | STR               | World_Topo_Map | []       |
| height   | INT               | 600            | []       |
| width    | INT               | 800            | []       |
| zip      | ARRAY[INT] or INT |                | [x]      |
| union    | BOOL              |                | []       |

### Union

| Params | Prev                                         |
| ------ | -------------------------------------------- |
| 1      | <img src="img/union.webp" height="250"/>     |
| 0      | <img src="img/not-union.webp" height="250"/> |

### Colors

| Params | Prev                                      |
| ------ | ----------------------------------------- |
| 0E8BDE | <img src="img/0E8BDE.webp" height="250"/> |
| fdbb2d | <img src="img/fdbb2d.webp" height="250"/> |

### Styles

| Params                | Prev                                                     |
| --------------------- | -------------------------------------------------------- |
| ESRI_Standard         | <img src="img/ESRI_Standard.webp" height="250"/>         |
| Positron              | <img src="img/Positron.webp" height="250"/>              |
| Voyager               | <img src="img/Voyager.webp" height="250"/>               |
| Waze                  | <img src="img/Waze.webp" height="250"/>                  |
| World_Light_Gray_Base | <img src="img/World_Light_Gray_Base.webp" height="250"/> |
| World_Topo_Map        | <img src="img/World_Topo_Map.webp" height="250"/>        |
